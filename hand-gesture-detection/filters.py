"""
Professional filtering algorithms for smooth hand tracking
Implements One Euro Filter and Kalman Filter
"""
import numpy as np
import math
from collections import deque


class OneEuroFilter:
    """
    One Euro Filter for low-latency smoothing
    Paper: "1€ Filter: A Simple Speed-based Low-pass Filter for Noisy Input in Interactive Systems"
    """
    def __init__(self, freq=30, mincutoff=1.0, beta=0.007, dcutoff=1.0):
        """
        freq: sampling frequency (Hz)
        mincutoff: minimum cutoff frequency (Hz) - decrease to reduce jitter
        beta: speed coefficient - increase to reduce lag
        dcutoff: cutoff frequency for derivative
        """
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None
    
    def __call__(self, x, t=None):
        """Filter a new value"""
        if t is None:
            t = 0
        
        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = 0
            self.t_prev = t
            return x
        
        # Calculate time delta
        dt = t - self.t_prev if t != self.t_prev else 1.0 / self.freq
        
        # Calculate derivative
        dx = (x - self.x_prev) / dt
        
        # Smooth derivative
        edx = self._smoothing_factor(dt, self.dcutoff)
        dx_hat = self._exponential_smoothing(dx, self.dx_prev, edx)
        
        # Calculate cutoff frequency
        cutoff = self.mincutoff + self.beta * abs(dx_hat)
        
        # Smooth value
        ex = self._smoothing_factor(dt, cutoff)
        x_hat = self._exponential_smoothing(x, self.x_prev, ex)
        
        # Update state
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        
        return x_hat
    
    def _smoothing_factor(self, dt, cutoff):
        """Calculate smoothing factor"""
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
    
    def _exponential_smoothing(self, x, x_prev, alpha):
        """Apply exponential smoothing"""
        return alpha * x + (1 - alpha) * x_prev


class KalmanFilter:
    """
    Kalman Filter for predictive smoothing
    Predicts next position based on velocity model
    """
    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        """
        process_noise: how much we trust the model (lower = trust model more)
        measurement_noise: how much we trust measurements (lower = trust measurements more)
        """
        # State: [position, velocity]
        self.x = np.array([0.0, 0.0])
        
        # State covariance
        self.P = np.eye(2) * 1000
        
        # State transition matrix (constant velocity model)
        self.F = np.array([[1, 1],
                          [0, 1]])
        
        # Measurement matrix (we only measure position)
        self.H = np.array([[1, 0]])
        
        # Process noise covariance
        self.Q = np.eye(2) * process_noise
        
        # Measurement noise covariance
        self.R = np.array([[measurement_noise]])
        
        self.initialized = False
    
    def update(self, measurement):
        """Update filter with new measurement"""
        if not self.initialized:
            self.x[0] = measurement
            self.initialized = True
            return measurement
        
        # Prediction step
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        # Update step
        y = measurement - (self.H @ self.x)[0]  # Innovation
        S = (self.H @ self.P @ self.H.T + self.R)[0, 0]  # Innovation covariance
        K = (self.P @ self.H.T) / S  # Kalman gain
        
        self.x = self.x + K.flatten() * y
        self.P = (np.eye(2) - K @ self.H) @ self.P
        
        return self.x[0]


class MultiFrameAverager:
    """
    Multi-frame averaging with outlier rejection
    Keeps last N frames, removes outliers, returns average
    """
    def __init__(self, window_size=8, drop_outliers=2):
        """
        window_size: number of frames to average
        drop_outliers: number of min/max values to drop
        """
        self.window_size = window_size
        self.drop_outliers = drop_outliers
        self.buffer = deque(maxlen=window_size)
    
    def update(self, value):
        """Add new value and return filtered result"""
        self.buffer.append(value)
        
        if len(self.buffer) < self.window_size:
            # Not enough data yet, return current value
            return value
        
        # Convert to sorted array
        sorted_values = sorted(self.buffer)
        
        # Drop outliers from both ends
        if self.drop_outliers > 0 and len(sorted_values) > 2 * self.drop_outliers:
            trimmed = sorted_values[self.drop_outliers:-self.drop_outliers]
        else:
            trimmed = sorted_values
        
        # Return average
        return sum(trimmed) / len(trimmed)


class AdaptiveFilter:
    """
    Adaptive filter that combines multiple techniques
    Uses One Euro Filter + Kalman Filter + Multi-frame averaging
    """
    def __init__(self):
        self.one_euro_x = OneEuroFilter(freq=30, mincutoff=0.5, beta=0.01)
        self.one_euro_y = OneEuroFilter(freq=30, mincutoff=0.5, beta=0.01)
        self.kalman_x = KalmanFilter(process_noise=0.005, measurement_noise=0.05)
        self.kalman_y = KalmanFilter(process_noise=0.005, measurement_noise=0.05)
        self.averager_x = MultiFrameAverager(window_size=5, drop_outliers=1)
        self.averager_y = MultiFrameAverager(window_size=5, drop_outliers=1)
        self.frame_count = 0
    
    def filter(self, x, y):
        """Apply all filters in sequence"""
        self.frame_count += 1
        
        # Step 1: Multi-frame averaging (removes outliers)
        x_avg = self.averager_x.update(x)
        y_avg = self.averager_y.update(y)
        
        # Step 2: Kalman filter (predictive smoothing)
        x_kalman = self.kalman_x.update(x_avg)
        y_kalman = self.kalman_y.update(y_avg)
        
        # Step 3: One Euro filter (velocity-adaptive smoothing)
        x_final = self.one_euro_x(x_kalman, self.frame_count / 30.0)
        y_final = self.one_euro_y(y_kalman, self.frame_count / 30.0)
        
        return x_final, y_final
    
    def reset(self):
        """Reset all filters"""
        self.one_euro_x = OneEuroFilter(freq=30, mincutoff=0.5, beta=0.01)
        self.one_euro_y = OneEuroFilter(freq=30, mincutoff=0.5, beta=0.01)
        self.kalman_x = KalmanFilter(process_noise=0.005, measurement_noise=0.05)
        self.kalman_y = KalmanFilter(process_noise=0.005, measurement_noise=0.05)
        self.averager_x.buffer.clear()
        self.averager_y.buffer.clear()
        self.frame_count = 0
