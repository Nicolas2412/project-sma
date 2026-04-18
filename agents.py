################################################################################
# PROJET : SMA (Systèmes Multi-Agents) - Groupe 6
# DATE DE CRÉATION : 16/03/2026
#
# MEMBRES DU GROUPE :
#   - Nicolas Charronnière
#   - Paul Guimbert
#
# FILE: agents.py
################################################################################

import random
from objects import Waste, Radioactivity
from communication.agent.CommunicatingAgent import CommunicatingAgent
from communication.message.Message import Message
from communication.message.MessagePerformative import MessagePerformative
from strategies.naive_strategy import naive_deliberate, naive_deliberate_red
from strategies.random_strategy import random_deliberate
from strategies.smart_strategy import smart_deliberate, smart_deliberate_red, update_known_wastes
from strategies.communication_strategy import comm_deliberate

# ──────────────────────────────────────────────────────────────────────────────
# Base Robot — always inherits CommunicatingAgent
# ──────────────────────────────────────────────────────────────────────────────

class Robot(CommunicatingAgent):
    """Robot parent class. Inherits CommunicatingAgent so all robots have
    a name and mailbox regardless of strategy. Non-communicating strategies
    simply never send or read messages."""

    def __init__(self, model, name: str, cooldown: int = 3):
        super().__init__(model, name)

        self.wastes = {1: [], 2: [], 3: []}

        self.knowledge = {
            "current_pos":        None,
            "inventory":          self.wastes.copy(),
            "grid":               {},
            "cooldown_remaining": 0,
            "known_wastes":       {},   # used by smart + communicating
            "action_queue":       [],   # used by smart + communicating
            "target":             None, # used by smart + communicating
            "rendezvous":         None, # used by communicating only
        }

        self.cooldown = cooldown
        self.cooldown_remaining = 0
        self.current_percepts = None

    def step(self):
        if not self.current_percepts:
            self.current_percepts = self.model.get_percepts(self)
        self.update(self.current_percepts)
        self._process_messages()          # no-op for non-communicating strategies
        action = self.deliberate(self.knowledge)
        self.current_percepts = self.model.do(self, action)

    def update(self, percepts):
        self.knowledge["current_pos"]        = percepts["current_pos"]
        self.knowledge["inventory"]          = self.wastes.copy()
        self.knowledge["grid"].update(percepts["grid"])
        self.knowledge["cooldown_remaining"] = percepts.get("cooldown_remaining", 0)
        update_known_wastes(self.knowledge, percepts)  # always safe to call

    def _process_messages(self):
        """No-op by default. Overridden by _RendezvousMixin."""
        pass

    def deliberate(self, knowledge):
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Rendezvous mixin
# ──────────────────────────────────────────────────────────────────────────────

# How many steps a rendezvous can stay alive before being force-cancelled.
# This prevents agents from being permanently frozen if the other side
# silently disappears (e.g. picked up a second waste from the ground).
RENDEZVOUS_TIMEOUT = 40

class _RendezvousMixin:
    """Shared communication logic for GreenAgent / YellowAgent
    when strategy == 'communicating'.

    Protocol (PROPOSE → ACCEPT → COMMIT):
      • Any agent holding exactly 1 own-colour waste broadcasts PROPOSE.
      • A recipient that also holds exactly 1 own-colour waste and is free
        replies ACCEPT (no BFS check — routing is handled by comm_deliberate).
      • The requester takes the first ACCEPT, sets partner + target_pos,
        and confirms with COMMIT. Late ACCEPTs get CANCEL.
      • The requester navigates to the acceptor and drops its waste there.
      • The acceptor picks up the dropped waste and transforms.
      • A step counter guards against permanent freezes (RENDEZVOUS_TIMEOUT).
    """

    def _process_messages(self):
        rendezvous = self.knowledge["rendezvous"]
        my_name    = self.get_name()
        my_pos     = self.knowledge["current_pos"]
        inventory  = self.knowledge["inventory"]
        own_waste  = self.type

        # ── Timeout guard ────────────────────────────────────────────────────
        # Increment the step counter on every live rendezvous and cancel if it
        # has been running too long.  This catches the case where the partner
        # silently disappeared (e.g. picked up a second waste on its own).
        if rendezvous is not None:
            rendezvous["steps_waiting"] = rendezvous.get("steps_waiting", 0) + 1
            if rendezvous["steps_waiting"] > RENDEZVOUS_TIMEOUT:
                print(f"[{my_name}] TIMEOUT — cancelling rendezvous "
                      f"(role={rendezvous['role']}, partner={rendezvous['partner']})")
                if rendezvous["partner"] is not None:
                    self.send_message(Message(
                        my_name, rendezvous["partner"],
                        MessagePerformative.CANCEL, {}
                    ))
                self.knowledge["rendezvous"] = None
                rendezvous = None

        # ── Early-cancel for requester that lost its waste ───────────────────
        # Only fires while we are still waiting for the first ACCEPT
        # (target_pos is None). Once we have a confirmed partner and are
        # navigating, we let the journey complete regardless.
        if (rendezvous is not None and
                rendezvous["role"] == "requester" and
                rendezvous["target_pos"] is None):
            if len(inventory[own_waste]) != 1 or len(inventory[own_waste + 1]) != 0:
                print(f"[{my_name}] cancelling PROPOSE — inventory changed "
                      f"before any ACCEPT (inv={inventory})")
                if rendezvous["partner"] is not None:
                    self.send_message(Message(
                        my_name, rendezvous["partner"],
                        MessagePerformative.CANCEL, {}
                    ))
                self.knowledge["rendezvous"] = None
                rendezvous = None

        # ── Process inbox ────────────────────────────────────────────────────
        for msg in self.get_new_messages():
            perf    = msg.get_performative()
            sender  = msg.get_exp()
            content = msg.get_content()
            # Re-read in case an earlier message in this loop mutated it
            rendezvous = self.knowledge["rendezvous"]

            # ── PROPOSE ──────────────────────────────────────────────────────
            # Accept if: free, holding exactly 1 own waste, not self.
            # No BFS check here — routing is comm_deliberate's responsibility.
            if perf == MessagePerformative.PROPOSE:
                if (rendezvous is None and
                        len(inventory[own_waste]) == 1 and
                        len(inventory[own_waste + 1]) == 0 and
                        sender != my_name):
                    rendezvous = {
                        "role":          "acceptor",
                        "partner":       sender,
                        "target_pos":    content["pos"],  # requester's pos (info only)
                        "steps_waiting": 0,
                    }
                    self.knowledge["rendezvous"] = rendezvous
                    self.send_message(Message(
                        my_name, sender,
                        MessagePerformative.ACCEPT, {"pos": my_pos}
                    ))
                    print(f"[{my_name}] ACCEPT → {sender} "
                          f"(my_pos={my_pos}, requester_pos={content['pos']})")

            # ── ACCEPT ───────────────────────────────────────────────────────
            # Take the first ACCEPT; reject all subsequent ones.
            elif perf == MessagePerformative.ACCEPT:
                if (rendezvous is not None and
                        rendezvous["role"] == "requester" and
                        rendezvous["partner"] is None):
                    # First ACCEPT — commit unconditionally.
                    # BFS routing happens in comm_deliberate; if the path is not
                    # known yet the agent will explore until it finds one.
                    rendezvous["partner"]    = sender
                    rendezvous["target_pos"] = content["pos"]
                    self.knowledge["rendezvous"] = rendezvous
                    self.send_message(Message(
                        my_name, sender,
                        MessagePerformative.COMMIT, {"pos": my_pos}
                    ))
                    print(f"[{my_name}] COMMIT → {sender} "
                          f"(heading to {content['pos']})")

                elif (rendezvous is not None and
                        rendezvous["role"] == "requester" and
                        rendezvous["partner"] != sender):
                    # Late ACCEPT — already have a partner.
                    self.send_message(Message(
                        my_name, sender,
                        MessagePerformative.CANCEL, {}
                    ))

            # ── COMMIT ───────────────────────────────────────────────────────
            # Acceptor side: requester confirmed.  Nothing extra to do — the
            # acceptor will wait and pick up the waste when it arrives.
            elif perf == MessagePerformative.COMMIT:
                pass

            # ── CANCEL ───────────────────────────────────────────────────────
            elif perf == MessagePerformative.CANCEL:
                if rendezvous is not None and rendezvous["partner"] == sender:
                    print(f"[{my_name}] rendezvous CANCELLED by {sender}")
                    self.knowledge["rendezvous"] = None

    def _maybe_initiate_rendezvous(self, knowledge):
        """Broadcast PROPOSE to all same-type agents if we hold exactly
        1 own-colour waste and are not already in a rendezvous."""
        own_waste  = self.type
        inventory  = knowledge["inventory"]
        rendezvous = knowledge["rendezvous"]
        my_name    = self.get_name()
        my_pos     = knowledge["current_pos"]

        if rendezvous is not None:
            return
        if len(inventory[own_waste]) != 1 or len(inventory[own_waste + 1]) != 0:
            return

        target_class = type(self)
        sent = False
        for agent in self.model.agents:
            if isinstance(agent, target_class) and agent.get_name() != my_name:
                self.send_message(Message(
                    my_name, agent.get_name(),
                    MessagePerformative.PROPOSE, {"pos": my_pos}
                ))
                sent = True

        if sent:
            self.knowledge["rendezvous"] = {
                "role":          "requester",
                "partner":       None,
                "target_pos":    None,
                "steps_waiting": 0,
            }
            print(f"[{my_name}] PROPOSE broadcast (pos={my_pos}, "
                  f"inv={len(inventory[own_waste])} waste-{own_waste})")


# ──────────────────────────────────────────────────────────────────────────────
# GreenAgent
# ──────────────────────────────────────────────────────────────────────────────

class GreenAgent(_RendezvousMixin, Robot):

    def __init__(self, model, strategy: str = 'naive'):
        name = f"GreenAgent_{GreenAgent._next_id(model)}"
        super().__init__(model, name=name)
        self.type     = 1
        self.epsilon  = 0.05
        self.strategy = strategy

    @staticmethod
    def _next_id(model):
        if not hasattr(model, "_green_agent_counter"):
            model._green_agent_counter = 0
        model._green_agent_counter += 1
        return model._green_agent_counter

    def _process_messages(self):
        if self.strategy == 'communicating':
            _RendezvousMixin._process_messages(self)
        # else: no-op

    def deliberate(self, knowledge):
        if self.strategy == 'naive':
            return naive_deliberate(knowledge, low_waste=1, high_waste=2, epsilon=self.epsilon)
        elif self.strategy == 'random':
            return random_deliberate(knowledge)
        elif self.strategy == 'smart':
            return smart_deliberate(knowledge, low_waste=1, high_waste=2, epsilon=self.epsilon)
        elif self.strategy == 'communicating':
            self._maybe_initiate_rendezvous(knowledge)
            return comm_deliberate(knowledge, low_waste=1, high_waste=2, epsilon=self.epsilon)
        else:
            raise ValueError(f"Invalid strategy: {self.strategy}")


# ──────────────────────────────────────────────────────────────────────────────
# YellowAgent
# ──────────────────────────────────────────────────────────────────────────────

class YellowAgent(_RendezvousMixin, Robot):

    def __init__(self, model, strategy: str = 'naive'):
        name = f"YellowAgent_{YellowAgent._next_id(model)}"
        super().__init__(model, name=name)
        self.type     = 2
        self.epsilon  = 0.05
        self.strategy = strategy

    @staticmethod
    def _next_id(model):
        if not hasattr(model, "_yellow_agent_counter"):
            model._yellow_agent_counter = 0
        model._yellow_agent_counter += 1
        return model._yellow_agent_counter

    def _process_messages(self):
        if self.strategy == 'communicating':
            _RendezvousMixin._process_messages(self)

    def deliberate(self, knowledge):
        if self.strategy == 'naive':
            return naive_deliberate(knowledge, low_waste=2, high_waste=3, epsilon=self.epsilon)
        elif self.strategy == 'random':
            return random_deliberate(knowledge)
        elif self.strategy == 'smart':
            return smart_deliberate(knowledge, low_waste=2, high_waste=3, epsilon=self.epsilon)
        elif self.strategy == 'communicating':
            self._maybe_initiate_rendezvous(knowledge)
            return comm_deliberate(knowledge, low_waste=2, high_waste=3, epsilon=self.epsilon)
        else:
            raise ValueError(f"Invalid strategy: {self.strategy}")


# ──────────────────────────────────────────────────────────────────────────────
# RedAgent
# ──────────────────────────────────────────────────────────────────────────────

class RedAgent(Robot):

    def __init__(self, model, strategy: str = 'naive'):
        name = f"RedAgent_{RedAgent._next_id(model)}"
        super().__init__(model, name=name)
        self.type     = 3
        self.strategy = strategy

    @staticmethod
    def _next_id(model):
        if not hasattr(model, "_red_agent_counter"):
            model._red_agent_counter = 0
        model._red_agent_counter += 1
        return model._red_agent_counter

    def deliberate(self, knowledge):
        if self.strategy == 'naive':
            return naive_deliberate_red(knowledge)
        elif self.strategy == 'random':
            return random_deliberate(knowledge, is_red=True)
        elif self.strategy in ('smart', 'communicating'):
            return smart_deliberate_red(knowledge)
        else:
            raise ValueError(f"Invalid strategy: {self.strategy}")