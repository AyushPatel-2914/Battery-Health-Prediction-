import subprocess
import sys

# Run main.py, capturing all output
result = subprocess.run(
    [sys.executable, '-3', 'Simulation_data\\Monthly_simulation\\main.py'],
    capture_output=True,
    text=True,
    cwd='c:\\Users\\HP\\OneDrive\\Desktop\\Jhil\\Battery-Health-Prediction-'
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
