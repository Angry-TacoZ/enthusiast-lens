# Full Product Expansion: Preserved V1 92-Field Schema

The original V1 schema remains the product-scale expansion path. It was useful
for exploring configuration-aware enthusiast intelligence, but benchmark
execution showed that its 91 researched fields require four grounded research
batches and four reconciliation batches per vehicle. For the weekend hackathon,
the active evaluated task is the separate, versioned Core 24 catalog.

This is evidence-driven scope reduction, not a deletion or a claim that the
product-scale work was a mistake. The authoritative machine-readable source is
[`evals/task_definition/v1_objective_field_catalog.json`](../evals/task_definition/v1_objective_field_catalog.json).
The identifiers below are reproduced directly from that catalog; no renamed
parallel list is maintained.

## Audio

- `audio.amplifier_power_w`
- `audio.headrest_speakers`
- `audio.speaker_count`
- `audio.subwoofer`
- `audio.system_brand`

## Brakes, Wheels and Tires

- `brakes_wheels_and_tires.base_tire`
- `brakes_wheels_and_tires.base_wheel_size`
- `brakes_wheels_and_tires.front_brake_type`
- `brakes_wheels_and_tires.front_rotor_diameter_in`
- `brakes_wheels_and_tires.rear_brake_type`
- `brakes_wheels_and_tires.rear_rotor_diameter_in`
- `brakes_wheels_and_tires.tire_size`
- `brakes_wheels_and_tires.tire_type`
- `brakes_wheels_and_tires.wheel_size`

## Configuration Dependencies

- `configuration_dependencies.autopilot_hardware_transition`
- `configuration_dependencies.cargurus_acc_claim`
- `configuration_dependencies.digital_instrument_cluster`
- `configuration_dependencies.engine_family_output`
- `configuration_dependencies.equipment_group_201a_equipped`
- `configuration_dependencies.ford_safe_and_smart_package_equipped`
- `configuration_dependencies.high_performance_package_content`
- `configuration_dependencies.high_performance_package_equipped`
- `configuration_dependencies.manual_vs_automatic_performance_hardware`
- `configuration_dependencies.official_trim_name`
- `configuration_dependencies.same_engine_family_contamination`
- `configuration_dependencies.track_package`
- `configuration_dependencies.track_package_equipped`
- `configuration_dependencies.transmission_specific_awd`

## Driver Assistance and Highway Automation

- `driver_assistance_and_highway_automation.acc_brakes_to_stop`
- `driver_assistance_and_highway_automation.acc_hold_behavior`
- `driver_assistance_and_highway_automation.acc_max_set_speed_mph`
- `driver_assistance_and_highway_automation.acc_min_operating_speed_mph`
- `driver_assistance_and_highway_automation.acc_min_set_speed_mph`
- `driver_assistance_and_highway_automation.acc_system_name`
- `driver_assistance_and_highway_automation.active_safety_suite`
- `driver_assistance_and_highway_automation.adaptive_cruise_control`
- `driver_assistance_and_highway_automation.fsd_hardware_capability`
- `driver_assistance_and_highway_automation.hands_free_highway_assist`
- `driver_assistance_and_highway_automation.hardware_generation`
- `driver_assistance_and_highway_automation.lane_centering`
- `driver_assistance_and_highway_automation.lane_departure_warning`
- `driver_assistance_and_highway_automation.lane_following_assist`
- `driver_assistance_and_highway_automation.lane_keeping_assist`
- `driver_assistance_and_highway_automation.system_name`

## Drivetrain and Differentials

- `drivetrain_and_differentials.available_layouts`
- `drivetrain_and_differentials.center_system`
- `drivetrain_and_differentials.four_wheel_drive_system`
- `drivetrain_and_differentials.layout`
- `drivetrain_and_differentials.locking_differentials`
- `drivetrain_and_differentials.rear_limited_slip_differential`

## Engine and Measured Performance

- `engine_and_measured_performance.aspiration`
- `engine_and_measured_performance.battery_total_kwh`
- `engine_and_measured_performance.battery_usable_kwh`
- `engine_and_measured_performance.curb_weight`
- `engine_and_measured_performance.displacement_cc`
- `engine_and_measured_performance.engine_configuration`
- `engine_and_measured_performance.exhaust.active_valve_performance_exhaust`
- `engine_and_measured_performance.exhaust.factory_performance_exhaust_availability`
- `engine_and_measured_performance.exhaust.fratzonic_chambered_exhaust`
- `engine_and_measured_performance.horsepower`
- `engine_and_measured_performance.horsepower_rpm`
- `engine_and_measured_performance.power_to_weight_hp_per_us_ton`
- `engine_and_measured_performance.powertrain_type`
- `engine_and_measured_performance.redline`
- `engine_and_measured_performance.system_horsepower`
- `engine_and_measured_performance.system_torque`
- `engine_and_measured_performance.torque`
- `engine_and_measured_performance.torque_rpm`
- `engine_and_measured_performance.zero_to_60_mph`

## Suspension, Axles and Chassis

- `suspension_axles_and_chassis.bilstein_dampers`
- `suspension_axles_and_chassis.dsc_track_mode`
- `suspension_axles_and_chassis.electronic_sway_bar_disconnect`
- `suspension_axles_and_chassis.four_wheel_independent`
- `suspension_axles_and_chassis.front_axle_type`
- `suspension_axles_and_chassis.front_shock_tower_brace`
- `suspension_axles_and_chassis.front_suspension`
- `suspension_axles_and_chassis.induction_sound_enhancer`
- `suspension_axles_and_chassis.kinematic_posture_control`
- `suspension_axles_and_chassis.magnetic_ride_control_availability`
- `suspension_axles_and_chassis.rear_axle_type`
- `suspension_axles_and_chassis.rear_suspension`
- `suspension_axles_and_chassis.rs_shock_absorbers`
- `suspension_axles_and_chassis.sport_tuned_suspension`

## Transmission

- `transmission.available_transmissions`
- `transmission.control_type`
- `transmission.gear_count`
- `transmission.manual_mode`
- `transmission.manual_shift_mode`
- `transmission.mechanism`
- `transmission.paddle_shifters`
- `transmission.selector_sport_position`
- `transmission.sport_mode`

Vehicle-specific package and hardware fields remain valuable future product
depth. They are intentionally not universal Core 24 fields because they add
configuration-special-case complexity that is disproportionate for the
hackathon demo.
