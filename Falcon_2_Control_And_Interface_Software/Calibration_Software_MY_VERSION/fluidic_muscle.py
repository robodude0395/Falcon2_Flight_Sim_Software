import numpy as np
import matplotlib.pyplot as plt

class FluidicMuscle:
    def __init__(self, max_extension=100.0, min_extension=0.0, max_pressure=6000.0, load=0.0):
        """
        Initialize the fluidic muscle model.

        Parameters:
        - max_extension: Maximum possible extension (in mm or cm)
        - min_extension: Minimum possible extension (default = 0, resting state)
        - max_pressure: Maximum pressure input (in mbar, psi, etc.)
        - load: Load applied to the muscle (in Newtons or kg-force)
        """
        self.max_extension = max_extension
        self.min_extension = min_extension
        self.max_pressure = max_pressure
        self.load = load  # External force resisting muscle expansion
        self.current_extension = min_extension
        self.last_pressure = 0
        self.contracting = True  # Flag for contraction/relaxation

    def apply_pressure(self, pressure):
        """
        Apply pressure to the muscle and calculate the extension based on a hysteresis loop.

        Parameters:
        - pressure: Applied pressure (in mbar, psi, etc.)

        Returns:
        - New extension of the muscle.
        """
        if pressure > self.last_pressure:
            self.contracting = True
        elif pressure < self.last_pressure:
            self.contracting = False

        self.last_pressure = pressure

        # Normalize pressure between 0 and 1
        normalized_pressure = max(0, min(pressure / self.max_pressure, 1))

        # Load effect: More load reduces extension
        load_factor = 1 / (1 + 0.01 * self.load)  # More load → Less extension

        # Define different curves for contraction and relaxation
        if self.contracting:
            extension = self._hysteresis_function(normalized_pressure, contraction=True) * load_factor
        else:
            extension = self._hysteresis_function(normalized_pressure, contraction=False) * load_factor

        # Add small random variance for realism
        noise = np.random.uniform(-2, 2)
        extension += noise

        # Clamp extension between min and max
        self.current_extension = np.clip(extension, self.min_extension, self.max_extension)

        return self.current_extension

    def _hysteresis_function(self, norm_pressure, contraction=True):
        """
        Internal function to model the hysteresis effect during contraction and relaxation.

        Parameters:
        - norm_pressure: Pressure normalized between 0 and 1
        - contraction: Boolean flag for contraction phase

        Returns:
        - Extension value
        """
        if contraction:
            return self.max_extension * (norm_pressure ** 1.5)  # Steeper response
        else:
            return self.max_extension * (norm_pressure ** 0.5)  # Gentler response

"""
# Example usage with hysteresis plotting
if __name__ == "__main__":
    muscle_10kg = FluidicMuscle(max_extension=100.0, max_pressure=6000.0, load=10.0)  # No Load
    muscle_25kg = FluidicMuscle(max_extension=100.0, max_pressure=6000.0, load=25.0)  # 25kg Load
    muscle_40kg = FluidicMuscle(max_extension=100.0, max_pressure=6000.0, load=40.0)  # 40kg Load

    # Simulated pressure cycle: Increase then decrease
    pressures = list(range(0, 6001, 200)) + list(range(6000, -1, -200))  
    extensions_10kg = []
    extension_25kg = []
    extension_40kg = []

    for p in pressures:
        extensions_10kg.append(muscle_10kg.apply_pressure(p))
        extension_25kg.append(muscle_25kg.apply_pressure(p))
        extension_40kg.append(muscle_40kg.apply_pressure(p))

    # Plot the hysteresis loop
    plt.figure(figsize=(10, 6))

    # No Load Hysteresis
    plt.plot(pressures[:len(pressures)//2], extensions_10kg[:len(extensions_10kg)//2], 'bo-', label="10kg - Contraction")
    plt.plot(pressures[len(pressures)//2:], extensions_10kg[len(extensions_10kg)//2:], 'ro-', label="10kg - Relaxation")

    # Heavy Load Hysteresis
    plt.plot(pressures[:len(pressures)//2], extension_25kg[:len(extension_25kg)//2], marker='^', label="25kg - Contraction")
    plt.plot(pressures[len(pressures)//2:], extension_25kg[len(extension_25kg)//2:], marker='^', label="25kg - Relaxation")

    # Heavy Load Hysteresis
    plt.plot(pressures[:len(pressures)//2], extension_40kg[:len(extension_40kg)//2], 'bs-', label="40kg - Contraction")
    plt.plot(pressures[len(pressures)//2:], extension_40kg[len(extension_40kg)//2:], 'rs-', label="40kg - Relaxation")

    plt.xlabel("Pressure (mbar)")
    plt.ylabel("Extension (cm)")
    plt.title("Fluidic Muscle Hysteresis Loop with Load Effect")
    plt.legend()
    plt.grid()
    plt.show()
"""