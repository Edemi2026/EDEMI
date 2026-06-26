import lgpio

class LgpioWrapper:
    HIGH = 1
    LOW = 0
    OUT = 1
    IN = 0
    BCM = 11
    BOARD = 10

    def __init__(self):
        self.h = lgpio.gpiochip_open(0)
        self._setup_pins = []

    def setmode(self, mode):
        pass

    def setwarnings(self, flag):
        pass

    def setup(self, pin, mode, initial=None):
        if mode == self.OUT:
            lgpio.gpio_claim_output(self.h, pin)
            if initial is not None:
                lgpio.gpio_write(self.h, pin, initial)
        self._setup_pins.append(pin)

    def output(self, pin, value):
        lgpio.gpio_write(self.h, pin, value)

    def input(self, pin):
        return lgpio.gpio_read(self.h, pin)

    def cleanup(self, pins=None):
        if pins is None:
            pins = self._setup_pins
        if isinstance(pins, int):
            pins = [pins]
        for pin in pins:
            try:
                lgpio.gpio_free(self.h, pin)
            except:
                pass
