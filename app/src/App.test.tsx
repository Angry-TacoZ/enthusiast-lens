import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { App } from './App'
import { recordedRun } from './data/recordedRun'

describe('standalone judge UI', () => {
  it('keeps the local canonical record aligned with the complete Core 24 field set', () => {
    expect(recordedRun.facts.map((fact) => fact.field_id)).toEqual([
      'audio.amplifier_power_w',
      'audio.subwoofer',
      'brakes_wheels_and_tires.rotor_diameters_in',
      'brakes_wheels_and_tires.default_tire',
      'brakes_wheels_and_tires.braking_70_to_0_mph_ft',
      'driver_assistance_and_highway_automation.adaptive_cruise_control',
      'driver_assistance_and_highway_automation.acc_full_stop_and_go',
      'driver_assistance_and_highway_automation.active_lane_centering',
      'drivetrain_and_differentials.layout',
      'drivetrain_and_differentials.limited_slip_differential',
      'engine_and_measured_performance.displacement_l',
      'engine_and_measured_performance.aspiration',
      'engine_and_measured_performance.horsepower',
      'engine_and_measured_performance.torque_lb_ft',
      'engine_and_measured_performance.curb_weight_lb',
      'engine_and_measured_performance.pounds_per_horsepower',
      'engine_and_measured_performance.zero_to_60_mph',
      'engine_and_measured_performance.skidpad_g',
      'energy_storage.capacity',
      'transmission.type',
      'transmission.gear_count',
      'transmission.manual_shifting_from_selector',
      'transmission.paddle_shifters',
      'suspension_axles_and_chassis.suspension_layout',
    ])
  })

  it('loads a Core 24 analysis and opens its evidence inspector', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /open analysis/i }))

    expect(await screen.findByRole('heading', { name: /2026 mazda mx-5 miata/i })).toBeInTheDocument()
    expect(screen.getByText(/19\s*\/\s*24/)).toBeInTheDocument()
    expect(screen.getByText(/configuration analysis/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /inspect horsepower evidence/i }))
    const inspector = screen.getByRole('complementary', { name: /fact evidence/i })
    expect(within(inspector).getByRole('heading', { name: 'Horsepower' })).toBeInTheDocument()
    expect(within(inspector).getByText('181 hp')).toBeInTheDocument()
    expect(within(inspector).getAllByRole('link', { name: /open source/i })[0]).toHaveAttribute(
      'href',
      'https://www.mazdausa.com/vehicles/mx-5-miata/compare-vehicle-specs-and-trims',
    )
  })

  it('exposes the car enthusiast mark as a labeled image for assistive technology', () => {
    render(<App />)
    expect(screen.getByRole('img', { name: /animated sports car mark/i })).toBeInTheDocument()
  })

  it('does not invent a Hybrid result when no validated artifact exists', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: 'Hybrid' }))
    await user.click(screen.getByRole('button', { name: /review vehicle/i }))

    expect(await screen.findByRole('heading', { name: /hybrid analysis unavailable/i })).toBeInTheDocument()
    expect(screen.queryByText(/correct enthusiast fact coverage/i)).not.toBeInTheDocument()
  })
})
