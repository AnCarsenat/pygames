import pygame

DIRECTIONS = ("up", "down", "left", "right")
ACTIONS = DIRECTIONS + ("action", "start")

STICK_DEADZONE = 0.25
STICK_PRESS = 0.5
STICK_RELEASE = 0.35
PAD_ACTION_BUTTONS = (0, 1, 2, 3)
PAD_START_BUTTONS = (6, 7, 9)

KEYSETS = [
    {"up": pygame.KSCAN_W, "down": pygame.KSCAN_S, "left": pygame.KSCAN_A,
     "right": pygame.KSCAN_D, "action": pygame.KSCAN_SPACE},
    {"up": pygame.KSCAN_UP, "down": pygame.KSCAN_DOWN, "left": pygame.KSCAN_LEFT,
     "right": pygame.KSCAN_RIGHT, "action": pygame.KSCAN_RSHIFT},
    {"up": pygame.KSCAN_I, "down": pygame.KSCAN_K, "left": pygame.KSCAN_J,
     "right": pygame.KSCAN_L, "action": pygame.KSCAN_O},
    {"up": pygame.KSCAN_KP_8, "down": pygame.KSCAN_KP_5, "left": pygame.KSCAN_KP_4,
     "right": pygame.KSCAN_KP_6, "action": pygame.KSCAN_KP_0},
    {"up": pygame.KSCAN_T, "down": pygame.KSCAN_G, "left": pygame.KSCAN_F,
     "right": pygame.KSCAN_H, "action": pygame.KSCAN_Y},
]

SPECIAL_LABELS = {
    pygame.KSCAN_SPACE:"SPACE",
    pygame.KSCAN_UP: "UP", pygame.KSCAN_DOWN: "DOWN",
    pygame.KSCAN_LEFT: "LEFT", pygame.KSCAN_RIGHT: "RIGHT",
    pygame.KSCAN_RSHIFT: "R-SHIFT",
    pygame.KSCAN_KP_0: "NUM 0", pygame.KSCAN_KP_4: "NUM 4", pygame.KSCAN_KP_5: "NUM 5",
    pygame.KSCAN_KP_6: "NUM 6", pygame.KSCAN_KP_8: "NUM 8",
}
AZERTY_SWAPS = {pygame.KSCAN_W: "Z", pygame.KSCAN_A: "Q", pygame.KSCAN_Q: "A", pygame.KSCAN_Z: "W"}


def default_labels(layout):
    labels = {pygame.KSCAN_A + i: chr(ord("A") + i) for i in range(26)}
    labels.update(SPECIAL_LABELS)
    if layout == "azerty":
        labels.update(AZERTY_SWAPS)
    return labels


class Controls:
    color_index = 0

    def __init__(self):
        self._down = set()
        self._new_presses = set()
        self._new_releases = set()
        self._held = frozenset()
        self._pressed = frozenset()
        self._released = frozenset()

    def _set(self, action, down):
        if down and action not in self._down:
            self._down.add(action)
            self._new_presses.add(action)
        elif not down and action in self._down:
            self._down.discard(action)
            self._new_releases.add(action)

    def release_all(self):
        for action in list(self._down):
            self._set(action, False)

    def update(self):
        pressed = set(self._new_presses)
        taps = {a for a in self._new_releases & pressed if a not in self._down}

        self._pressed = frozenset(pressed)
        self._released = frozenset(self._new_releases - pressed)
        self._held = frozenset(self._down | pressed)
        self._new_presses = set()
        self._new_releases = taps

    def handle_event(self, event):
        pass

    def held(self, action):
        return action in self._held

    def pressed(self, action):
        return action in self._pressed

    def released(self, action):
        return action in self._released

    @property
    def axis_x(self):
        return int(self.held("right")) - int(self.held("left"))

    @property
    def axis_y(self):
        return int(self.held("down")) - int(self.held("up"))

    def direction(self):
        direction = pygame.Vector2(self.axis_x, self.axis_y)
        if direction.length_squared():
            direction.normalize_ip()
        return direction


class KeyboardControls(Controls):
    def __init__(self, index, keyset, labels):
        super().__init__()
        self.index = index
        self.color_index = index
        self.keyset = keyset
        self.labels = labels
        self.connected = True
        self._action_for = {scancode: action for action, scancode in keyset.items()}

    @property
    def name(self):
        return f"Keyboard {self.index + 1}"

    def label(self, action):
        return self.labels.get(self.keyset[action], "?")

    def describe(self):
        if self.keyset["up"] == pygame.KSCAN_UP:
            moves = "ARROWS"
        elif self.keyset["up"] == pygame.KSCAN_KP_8:
            moves = "NUMPAD 8 4 5 6"
        else:
            moves = " ".join(self.label(a) for a in ("up", "left", "down", "right"))
        return f"{moves}  +  {self.label('action')}"

    @property
    def join_hint(self):
        return self.label("action")

    def handle_event(self, event):
        if event.type not in (pygame.KEYDOWN, pygame.KEYUP):
            return
        action = self._action_for.get(event.scancode)
        if action:
            self._set(action, event.type == pygame.KEYDOWN)


class GamepadControls(Controls):
    def __init__(self, joystick, number, color_index):
        super().__init__()
        self.number = number
        self.color_index = color_index
        self.stick = pygame.Vector2()
        self.hat = (0, 0)
        self.buttons = set()
        self.attach(joystick)

    def attach(self, joystick):
        self.joystick = joystick
        self.instance_id = joystick.get_instance_id()
        self.guid = joystick.get_guid()
        self.device_name = joystick.get_name()
        self.connected = True

    def disconnect(self):
        self.connected = False
        self.stick.update(0, 0)
        self.hat = (0, 0)
        self.buttons.clear()
        self.release_all()

    @property
    def name(self):
        return f"Gamepad {self.number}"

    def describe(self):
        return f"STICK / D-PAD  +  A   ({self.device_name[:22]})"

    @property
    def join_hint(self):
        return "A"

    def handle_event(self, event):
        if getattr(event, "instance_id", None) != self.instance_id:
            return
        if event.type == pygame.JOYAXISMOTION and event.axis in (0, 1):
            self.stick[event.axis] = event.value
        elif event.type == pygame.JOYHATMOTION and event.hat == 0:
            self.hat = event.value
        elif event.type == pygame.JOYBUTTONDOWN:
            self.buttons.add(event.button)
        elif event.type == pygame.JOYBUTTONUP:
            self.buttons.discard(event.button)
        else:
            return
        self._sync()

    def _sync(self):
        hat_x, hat_y = self.hat
        self._set("left", hat_x < 0 or self._stick_past("left", -self.stick.x))
        self._set("right", hat_x > 0 or self._stick_past("right", self.stick.x))
        self._set("up", hat_y > 0 or self._stick_past("up", -self.stick.y))
        self._set("down", hat_y < 0 or self._stick_past("down", self.stick.y))
        self._set("action", any(b in self.buttons for b in PAD_ACTION_BUTTONS))
        self._set("start", any(b in self.buttons for b in PAD_START_BUTTONS))

    def _stick_past(self, action, amount):
        threshold = STICK_RELEASE if action in self._down else STICK_PRESS
        return amount > threshold

    def direction(self):
        if self.stick.length() > STICK_DEADZONE:
            direction = pygame.Vector2(self.stick)
            if direction.length() > 1:
                direction.normalize_ip()
            return direction
        return super().direction()


class InputManager:
    def __init__(self, layout="azerty"):
        pygame.joystick.init()
        self.labels = default_labels(layout)
        self.keyboards = [KeyboardControls(i, keyset, self.labels) for i, keyset in enumerate(KEYSETS)]
        self.gamepads = []

    @property
    def devices(self):
        return self.keyboards + [pad for pad in self.gamepads if pad.connected]

    def _all(self):
        return self.keyboards + self.gamepads

    def handle_event(self, event):
        if event.type == pygame.JOYDEVICEADDED:
            self._connect(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self._disconnect(event.instance_id)
        elif event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
            for controls in self._all():
                controls.release_all()
        elif event.type == pygame.KEYDOWN:
            self._learn_label(event)

        for controls in self._all():
            controls.handle_event(event)

    def update(self):
        for controls in self._all():
            controls.update()

    def any_pressed(self, action, among=None):
        return any(c.pressed(action) for c in (among if among is not None else self.devices))

    def _connect(self, device_index):
        joystick = pygame.joystick.Joystick(device_index)
        instance_id = joystick.get_instance_id()
        if any(pad.connected and pad.instance_id == instance_id for pad in self.gamepads):
            return
        for pad in self.gamepads:
            if not pad.connected and pad.guid == joystick.get_guid():
                pad.attach(joystick)
                return
        number = len(self.gamepads) + 1
        self.gamepads.append(GamepadControls(joystick, number, len(self.keyboards) + number - 1))

    def _disconnect(self, instance_id):
        for pad in self.gamepads:
            if pad.connected and pad.instance_id == instance_id:
                pad.disconnect()

    def _learn_label(self, event):
        name = pygame.key.name(event.key)
        if name and len(name) <= 8:
            self.labels[event.scancode] = name.upper()
