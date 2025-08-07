import matplotlib.pyplot as plt
import numpy as np

# Script to run through heat transfer calculations
# to estimate the temperature that particles will be at when the reach the passive sampler
# Inspired by a particle in the S3-D field that appears to be fully embedded in the carbon tape

# 100% Known physical constants
air_gas_constant = 287.058  # J / kg * K
air_ref_visc = 1.716e-5  # Ns/m^2
air_ref_temp = 273  # K
visc_sutherland_const = 111  # K
air_ref_cond = 0.0241  # W / m K
cond_sutherland_const = 194  # K
# air_specific_heat = 1.4  # assuming it's an ideal gas; right for most temperatures
pi = 3.14159265

# Parameters
wind_speed = 2  # m/s
distance = 500  # m
particle_dia = 34.8e-6  # m
env_temp = 300  # K
air_pressure = 101325  # Pa, assuming standard pressure

# MgAl2O4 Particle parameters
# particle_thermal_cond = 0.15  # W / m * K
# particle_density = 3640  # kg/m^3
# particle_specific_heat = 290  # J/kg * K
# particle_start_temp = 1366.5  # K

# Pure MgAl alloy particle parameters
particle_thermal_cond = 100  # W / m K
particle_start_temp = 1366.5  # K
particle_density = 2726.0 - 0.99 * (particle_start_temp + env_temp) / 2
particle_specific_heat = 1000  # J / kg K

# Begin calculation
air_density = air_pressure / (air_gas_constant * env_temp)  # Ideal gas law
print(f"Air density: {air_density}")
particle_mass = 4/3 * pi * (particle_dia/2)**3 * particle_density  # kg
print(f"Particle mass: {particle_mass}")
particle_surface_area = 4 * pi * (particle_dia/2)**2
print(f"Particle surface area: {particle_surface_area}")
travel_time = distance / wind_speed

air_dyn_visc = air_ref_visc * (env_temp / air_ref_temp)**1.5 * ((air_ref_temp + visc_sutherland_const) / (env_temp + visc_sutherland_const))  # Ns/m^2 or kg/m*s; Sutherland's Formula
print(f"Air dynamic viscosity: {air_dyn_visc}")
air_reynolds = air_density * wind_speed * particle_dia / air_dyn_visc
print(f"Air Reynolds number: {air_reynolds}")
air_thermal_cond = air_ref_cond * (env_temp / air_ref_temp)**1.5 * ((air_ref_temp + cond_sutherland_const) / (env_temp + cond_sutherland_const))  # W / m * k; Sutherland's Formula
print(f"Air thermal conductivity: {air_thermal_cond}")
# air_prandtl = air_dyn_visc * air_specific_heat / air_thermal_cond
air_prandtl = 0.71  # standard number for air at reasonable temperatures
air_nusselt = 2 + 0.4 * air_reynolds**0.5 * air_prandtl**(1/3)
print(f"Air Nusselt Number: {air_nusselt}")
air_conv_coef = air_thermal_cond * air_nusselt / particle_dia  # W / m^2 K
print(f"Air Convection Coefficient: {air_conv_coef}")
# Errors may be starting to accumulate
biot = air_conv_coef * particle_dia / particle_thermal_cond
print(f"Biot number: {biot}")

if biot < 0.1:  # Lumped model assumption
    # Results for Newton's Law of Cooling
    time_constant = particle_mass * particle_specific_heat / (air_conv_coef * particle_surface_area)
    print(f"Lumped time constant: {time_constant}s")

    time_range = np.linspace(0, travel_time, 100000)  # need to make this adaptive
    lumped_temp = env_temp + (particle_start_temp - env_temp) * np.exp(-time_range / time_constant)
    plt.plot(time_range * wind_speed, lumped_temp)
    plt.xlabel("Distance from Source (m)")
    plt.ylabel("Particle Temperature (K)")
    plt.title("Particle Temperature over Distance")
    plt.show()

else:
    print("Differential cooling not implemented yet")