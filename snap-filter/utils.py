class Stabilizer:
    def __init__(self, alpha=0.3):
        """
        Exponential Moving Average (EMA) Stabilizer.
        alpha: Smoothing factor between 0.0 and 1.0. Lower is smoother/slower, Higher is faster/more jittery.
        """
        self.alpha = alpha
        self.state = None

    def update(self, new_value):
        """
        Updates the moving average and returns the smoothed value.
        Works for single floats, or tuples/lists of numbers.
        """
        if self.state is None:
            self.state = new_value
        else:
            if isinstance(new_value, (tuple, list)):
                self.state = tuple(self.alpha * n + (1 - self.alpha) * o for n, o in zip(new_value, self.state))
            else:
                self.state = self.alpha * new_value + (1 - self.alpha) * self.state
        return self.state

    def reset(self):
        self.state = None
