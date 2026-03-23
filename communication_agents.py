################################################################################
# PROJET : SMA (Systèmes Multi-Agents) - Groupe 6
# DATE DE CRÉATION : 16/03/2026
#
# MEMBRES DU GROUPE :
#   - Nicolas Charronnière
#   - Paul Guimbert
#
# FILE: communicating_agents.py
#
# COMMUNICATION PROTOCOL (green & yellow agents, symmetric for both):
#
#   Goal: two same-colour robots that each carry exactly 1 own-colour waste
#         coordinate so that one hands its waste to the other, enabling a
#         transform action.
#
#   Roles assigned per exchange:
#     • REQUESTER – the robot that initiates the negotiation (has 1 waste,
#                   no active rendezvous, and is not already an ACCEPTOR).
#     • ACCEPTOR   – the robot that agrees to collect and transform.
#
#   Message flow:
#     Step N   REQUESTER  →  PROPOSE     →  ACCEPTOR
#                  content: {"pos": (x,y)}
#                  meaning: "I have 1 waste; I'll bring it to you if you agree."
#
#     Step N   ACCEPTOR   →  ACCEPT      →  REQUESTER
#                  content: {"pos": (x,y)}
#                  meaning: "Agreed. Come to my position."
#
#     Step N+  REQUESTER  →  COMMIT      →  ACCEPTOR
#                  content: {"pos": (x,y)}
#                  meaning: "I confirm. Moving toward you."
#
#   Behaviour after handshake:
#     • REQUESTER navigates toward ACCEPTOR's position and drops its waste
#       when adjacent (puts it on the grid); then resets to normal behaviour.
#     • ACCEPTOR picks up the dropped waste on its cell (handled by normal
#       pick logic) and transforms once it holds 2 wastes.
#
#   Knowledge keys added:
#     "rendezvous": None  |  {"role": "requester"|"acceptor",
#                              "partner": <agent_name>,
#                              "target_pos": (x, y)}
#
# RED AGENTS:
#   Red agents inherit the communication scaffold (name, mailbox, helpers)
#   so you can wire up their specific protocol later without changing the
#   class hierarchy.  Their deliberate() is unchanged from agents.py.
################################################################################

import random
from objects import Waste, Radioactivity
from communication.agent.CommunicatingAgent import CommunicatingAgent
from communication.message.Message import Message
from communication.message.MessagePerformative import MessagePerformative


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _move_toward(current_pos, target_pos, possible_actions):
    """Return a move action one step closer to target_pos (Manhattan, x first),
    falling back to a random action if no directed move is in possible_actions."""
    cx, cy = current_pos
    tx, ty = target_pos
    dx = tx - cx
    dy = ty - cy

    preferred = []
    if dx > 0:
        preferred.append({"type": "move", "target": (cx + 1, cy)})
    elif dx < 0:
        preferred.append({"type": "move", "target": (cx - 1, cy)})
    if dy > 0:
        preferred.append({"type": "move", "target": (cx, cy + 1)})
    elif dy < 0:
        preferred.append({"type": "move", "target": (cx, cy - 1)})

    for action in preferred:
        if action in possible_actions:
            return action
    return random.choice(possible_actions)


# ---------------------------------------------------------------------------
# Base communicating robot
# ---------------------------------------------------------------------------

class Robot(CommunicatingAgent):
    """Robot parent class — replaces the non-communicating Robot from agents.py.

    Every robot now has:
      • a unique string name (required by MessageService.find_agent_from_name)
      • a mailbox (via CommunicatingAgent)
      • knowledge["rendezvous"] to track an active meeting negotiation
      • _process_messages() called at the top of each step to read mail and
        update knowledge before deliberation
    """

    # Class-level counter so names are unique without needing the model
    _instance_counter = 0

    def __init__(self, model, name: str, cooldown: int = 0):
        super().__init__(model, name)           # CommunicatingAgent.__init__

        # Real inventory — modified by model.do()
        self.wastes = {1: [], 2: [], 3: []}

        # Strictly structured knowledge base
        self.knowledge = {
            "current_pos": None,
            "inventory": self.wastes.copy(),
            "grid": {},
            "cooldown_remaining": 0,
            # rendezvous dict or None
            # {"role": "requester"|"acceptor", "partner": name, "target_pos": (x,y)}
            "rendezvous": None,
        }

        self.cooldown = cooldown
        self.cooldown_remaining = 0
        self.current_percepts = None

    # ------------------------------------------------------------------
    # Mesa step
    # ------------------------------------------------------------------

    def step(self):
        if not self.current_percepts:
            self.current_percepts = self.model.get_percepts(self)

        # 1. Integrate environment percepts into knowledge
        self.update(self.current_percepts)

        # 2. Read mail and update knowledge["rendezvous"] accordingly
        self._process_messages()

        # 3. Decide what to do (pure knowledge-based)
        action = self.deliberate(self.knowledge)

        # 4. Execute action, get new percepts
        self.current_percepts = self.model.do(self, action)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, percepts):
        self.knowledge["current_pos"] = percepts["current_pos"]
        self.knowledge["inventory"] = self.wastes.copy()
        self.knowledge["grid"].update(percepts["grid"])
        if "cooldown_remaining" in percepts:
            self.knowledge["cooldown_remaining"] = percepts["cooldown_remaining"]

    # ------------------------------------------------------------------
    # Message processing (base: no-op — subclasses override)
    # ------------------------------------------------------------------

    def _process_messages(self):
        """Read all new messages and update knowledge["rendezvous"].
        Override in subclasses that participate in a protocol."""
        pass

    # ------------------------------------------------------------------
    # Deliberate (base: no-op)
    # ------------------------------------------------------------------

    def deliberate(self, knowledge):
        """Override in subclasses."""
        pass


# ---------------------------------------------------------------------------
# Mixin: rendezvous protocol for GreenAgent / YellowAgent
# ---------------------------------------------------------------------------

class _RendezvousMixin:
    """Shared communication logic for same-colour robots that transform waste.

    Requires the host class to define:
      self.type  (int)  — waste colour handled (1 for green, 2 for yellow)
    """

    def _process_messages(self):
        """Parse inbox and update knowledge["rendezvous"]."""
        rendezvous = self.knowledge["rendezvous"]
        my_name = self.get_name()
        my_pos = self.knowledge["current_pos"]
        inventory = self.knowledge["inventory"]
        own_waste = self.type 
        
        if rendezvous is not None:
            own_waste = self.type
            if rendezvous["role"] == "requester":
                if len(inventory[own_waste]) != 1 or len(inventory[own_waste + 1]) != 0:
                    if rendezvous["partner"] is not None:
                        self.send_message(Message(
                            self.get_name(), rendezvous["partner"],
                            MessagePerformative.CANCEL,
                            {}
                        ))
                    self.knowledge["rendezvous"] = None

        for msg in self.get_new_messages():
            perf = msg.get_performative()
            sender = msg.get_exp()
            content = msg.get_content()

            # ── Incoming PROPOSE ──────────────────────────────────────────
            # Another robot with 1 waste proposes we act as acceptor.
            if perf == MessagePerformative.PROPOSE:
                # Only accept if:
                #   • we ourselves hold exactly 1 own-colour waste
                #   • we are not already engaged in a rendezvous
                #   • we are not the one who sent it (guard for broadcast)
                if (rendezvous is None and
                        len(inventory[own_waste]) == 1 and
                        sender != my_name):
                    rendezvous = {
                        "role": "acceptor",
                        "partner": sender,
                        "target_pos": content["pos"],  # requester's pos (info only)
                    }
                    self.knowledge["rendezvous"] = rendezvous
                    # Reply with ACCEPT, sending our own position
                    self.send_message(Message(
                        my_name, sender,
                        MessagePerformative.ACCEPT,
                        {"pos": my_pos}
                    ))

            # ── Incoming ACCEPT ───────────────────────────────────────────
            # Our PROPOSE was accepted; note acceptor's position as target.
            elif perf == MessagePerformative.ACCEPT:
                if (rendezvous is not None and
                        rendezvous["role"] == "requester" and
                        rendezvous["partner"] == sender):
                    rendezvous["target_pos"] = content["pos"]
                    self.knowledge["rendezvous"] = rendezvous
                    # Confirm with COMMIT
                    self.send_message(Message(
                        my_name, sender,
                        MessagePerformative.COMMIT,
                        {"pos": my_pos}
                    ))

            # ── Incoming COMMIT ───────────────────────────────────────────
            # Requester confirms it's on its way; nothing extra needed on
            # acceptor side — just wait and pick up the dropped waste.
            elif perf == MessagePerformative.COMMIT:
                pass  # acceptor already set; normal pick logic will handle it
            
            elif perf == MessagePerformative.CANCEL:
                if rendezvous is not None and rendezvous["partner"] == sender:
                    self.knowledge["rendezvous"] = None

    def _maybe_initiate_rendezvous(self, knowledge):
        """If we hold 1 own-colour waste and have no rendezvous, broadcast a
        PROPOSE to every same-type agent we know about via the model.

        Returns True if a PROPOSE was just sent (caller should fall through to
        movement this turn), False otherwise.
        """
        own_waste = self.type
        inventory = knowledge["inventory"]
        rendezvous = knowledge["rendezvous"]
        my_name = self.get_name()
        my_pos = knowledge["current_pos"]

        if rendezvous is not None:
            return False  # already negotiating
        if len(inventory[own_waste]) != 1 or len(inventory[own_waste + 1]) != 0:
            return False  # wrong inventory state

        # Broadcast PROPOSE to all same-colour robots
        target_class = type(self)
        sent = False
        for agent in self.model.agents:
            if isinstance(agent, target_class) and agent.get_name() != my_name:
                self.send_message(Message(
                    my_name, agent.get_name(),
                    MessagePerformative.PROPOSE,
                    {"pos": my_pos}
                ))
                sent = True

        if sent:
            # Mark ourselves as requester with no target yet (will be filled on ACCEPT)
            self.knowledge["rendezvous"] = {
                "role": "requester",
                "partner": None,   # will be set when first ACCEPT arrives
                "target_pos": None,
            }
        return sent

    def _rendezvous_deliberate(self, knowledge, possible_actions):
        """Return an action driven by the active rendezvous, or None if the
        rendezvous is complete / not applicable."""
        rendezvous = knowledge["rendezvous"]
        if rendezvous is None:
            return None

        own_waste = self.type
        inventory = knowledge["inventory"]
        current_pos = knowledge["current_pos"]
        role = rendezvous["role"]
        target_pos = rendezvous["target_pos"]

        # ── REQUESTER behaviour ───────────────────────────────────────────
        if role == "requester":
            if target_pos is None:
                # Waiting for ACCEPT reply — stay mobile but don't pick
                return random.choice(possible_actions)

            # Navigate toward acceptor
            if current_pos == target_pos:
                # We're on the acceptor's cell; drop waste and reset
                self.knowledge["rendezvous"] = None
                return {"type": "put"}

            return _move_toward(current_pos, target_pos, possible_actions)

        # ── ACCEPTOR behaviour ────────────────────────────────────────────
        if role == "acceptor":
            # Wait in place; once requester drops waste on our cell, normal
            # pick logic (handled outside this method) takes over.
            # Once we have 2 wastes the rendezvous is over.
            if len(inventory[own_waste]) == 2:
                self.knowledge["rendezvous"] = None
                return None  # fall through to transform

            # Stay put while waiting
            return {"type": "move", "target": current_pos}  # no-op move

        return None


# ---------------------------------------------------------------------------
# GreenAgent
# ---------------------------------------------------------------------------

class GreenAgent(_RendezvousMixin, Robot):
    """Green robot: collects green waste, transforms 2× green → 1× yellow."""

    def __init__(self, model, cooldown: int = 0):
        name = f"GreenAgent_{GreenAgent._next_id(model)}"
        super().__init__(model, name=name, cooldown=cooldown)
        self.type = 1
        self.epsilon = 0.05

    @staticmethod
    def _next_id(model):
        if not hasattr(model, "_green_agent_counter"):
            model._green_agent_counter = 0
        model._green_agent_counter += 1
        return model._green_agent_counter

    def deliberate(self, knowledge):
        x, y = knowledge["current_pos"]
        possible_actions = [
            {"type": "move", "target": (x, y + 1)},
            {"type": "move", "target": (x, y - 1)},
            {"type": "move", "target": (x + 1, y)},
            {"type": "move", "target": (x - 1, y)},
        ]
        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]
        on_cooldown = knowledge["cooldown_remaining"] > 0

        # 1. Transform if holding 2 own-colour wastes
        if len(inventory[1]) == 2:
            return {"type": "transform"}

        # 2. Put away transformed (yellow) waste into zone 2
        x, y = current_pos
        if len(inventory[2]) == 1 and knowledge["grid"].get((x + 1, y), {}).get("zone") == self.type + 1:
            return {"type": "put"}

        # 3. Rendezvous-driven action (navigate / wait / drop for partner)
        rv_action = self._rendezvous_deliberate(knowledge, possible_actions)
        if rv_action is not None:
            return rv_action

        # 4. Pick up waste on current cell (if not on cooldown)
        if (not on_cooldown and
                len(inventory[1]) < 2 and
                len(inventory[2]) == 0 and
                knowledge["grid"][current_pos]["wastes"][1] > 0):
            return {"type": "pick"}

        # 5. Navigate toward zone boundary when carrying yellow waste
        if len(inventory[2]) == 1:
            return {"type": "move", "target": (x + 1, y)}

        # 6. Try to initiate a rendezvous if holding 1 green waste
        self._maybe_initiate_rendezvous(knowledge)

        # 7. Random epsilon-drop of own-colour waste (triggers cooldown)
        if len(inventory[1]) == 1 and self.model.rng.random() < self.epsilon:
            return {"type": "put"}

        return random.choice(possible_actions)


# ---------------------------------------------------------------------------
# YellowAgent
# ---------------------------------------------------------------------------

class YellowAgent(_RendezvousMixin, Robot):
    """Yellow robot: collects yellow waste, transforms 2× yellow → 1× red."""

    def __init__(self, model, cooldown: int = 0):
        name = f"YellowAgent_{YellowAgent._next_id(model)}"
        super().__init__(model, name=name, cooldown=cooldown)
        self.type = 2
        self.epsilon = 0.05

    @staticmethod
    def _next_id(model):
        if not hasattr(model, "_yellow_agent_counter"):
            model._yellow_agent_counter = 0
        model._yellow_agent_counter += 1
        return model._yellow_agent_counter

    def deliberate(self, knowledge):
        x, y = knowledge["current_pos"]
        possible_actions = [
            {"type": "move", "target": (x, y + 1)},
            {"type": "move", "target": (x, y - 1)},
            {"type": "move", "target": (x + 1, y)},
            {"type": "move", "target": (x - 1, y)},
        ]
        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]
        on_cooldown = knowledge["cooldown_remaining"] > 0

        # 1. Transform if holding 2 own-colour wastes
        if len(inventory[2]) == 2:
            return {"type": "transform"}

        # 2. Put away transformed (red) waste into zone 3
        x, y = current_pos
        if len(inventory[3]) == 1 and knowledge["grid"].get((x + 1, y), {}).get("zone") == self.type + 1:
            return {"type": "put"}

        # 3. Rendezvous-driven action
        rv_action = self._rendezvous_deliberate(knowledge, possible_actions)
        if rv_action is not None:
            return rv_action

        # 4. Pick up waste on current cell (if not on cooldown)
        if (not on_cooldown and
                len(inventory[2]) < 2 and
                len(inventory[3]) == 0 and
                knowledge["grid"][current_pos]["wastes"][2] > 0):
            return {"type": "pick"}

        # 5. Navigate toward zone boundary when carrying red waste
        if len(inventory[3]) == 1:
            return {"type": "move", "target": (x + 1, y)}

        # 6. Try to initiate a rendezvous if holding 1 yellow waste
        self._maybe_initiate_rendezvous(knowledge)

        # 7. Random epsilon-drop
        if len(inventory[2]) == 1 and self.model.rng.random() < self.epsilon:
            return {"type": "put"}

        return random.choice(possible_actions)


# ---------------------------------------------------------------------------
# RedAgent
# ---------------------------------------------------------------------------

class RedAgent(Robot):
    """Red robot: collects red waste, deposits it in the disposal zone.

    Communication scaffold is inherited (name, mailbox, send/receive).
    Protocol to be implemented later via _process_messages() override.
    """

    def __init__(self, model):
        name = f"RedAgent_{RedAgent._next_id(model)}"
        super().__init__(model, name=name)
        self.type = 3

    @staticmethod
    def _next_id(model):
        if not hasattr(model, "_red_agent_counter"):
            model._red_agent_counter = 0
        model._red_agent_counter += 1
        return model._red_agent_counter

    def deliberate(self, knowledge):
        x, y = knowledge["current_pos"]
        possible_actions = [
            {"type": "move", "target": (x, y + 1)},
            {"type": "move", "target": (x, y - 1)},
            {"type": "move", "target": (x + 1, y)},
            {"type": "move", "target": (x - 1, y)},
        ]
        current_pos = knowledge["current_pos"]
        inventory = knowledge["inventory"]

        # Drop on disposal zone
        if (len(inventory[3]) == 1 and
                knowledge["grid"][current_pos]["drop"] and
                knowledge["grid"][current_pos]["zone"] == 3):
            return {"type": "put"}

        # Move right toward rightmost column
        if len(inventory[3]) == 1 and x < self.model.total_width - 1:
            return {"type": "move", "target": (x + 1, y)}

        # Wander along rightmost column searching for disposal zone
        if len(inventory[3]) == 1 and x == self.model.total_width - 1:
            return random.choice([
                {"type": "move", "target": (x, y + 1)},
                {"type": "move", "target": (x, y - 1)},
            ])

        # Pick up red waste
        if len(inventory[3]) == 0 and knowledge["grid"][current_pos]["wastes"][3] > 0:
            return {"type": "pick"}

        return random.choice(possible_actions)