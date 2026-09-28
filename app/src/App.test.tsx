import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { recordedRun } from './data/recordedRun'
import type { AnalysisClient } from './lib/analysisClient'

function fakeClient(): AnalysisClient {
  return {
    startAnalysis: vi.fn(async () => ({ id: 'test-job', status: 'succeeded' as const, result: structuredClone(recordedRun) })),
    getAnalysis: vi.fn(async () => ({ id: 'test-job', status: 'succeeded' as const, result: structuredClone(recordedRun) })),
  }
}

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

  it('lists every Core 24 vehicle family without fabricating analyses for them', async () => {
    const user = userEvent.setup()
    render(<App client={fakeClient()} />)

    const selector = screen.getByRole('combobox', { name: /vehicle context/i })
    expect(within(selector).getAllByRole('option')).toHaveLength(11)

    await user.selectOptions(selector, 'tesla-model-y')
    await user.click(screen.getByRole('button', { name: /review vehicle/i }))

    expect(await screen.findByRole('heading', { name: /2026 mazda mx-5 miata/i })).toBeInTheDocument()
  })

  it('loads a Core 24 analysis and opens its evidence inspector', async () => {
    const user = userEvent.setup()
    render(<App client={fakeClient()} />)

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
    render(<App client={fakeClient()} />)
    expect(screen.getByRole('img', { name: /animated sports car mark/i })).toBeInTheDocument()
  })

  it('does not invent a Hybrid result when no validated artifact exists', async () => {
    const user = userEvent.setup()
    render(<App client={fakeClient()} />)

    await user.click(screen.getByRole('button', { name: 'Hybrid' }))
    await user.click(screen.getByRole('button', { name: /review vehicle/i }))

    expect(await screen.findByRole('heading', { name: /2026 mazda mx-5 miata/i })).toBeInTheDocument()
  })

  it('does not render a report when the API reports a failed run', async () => {
    const user = userEvent.setup()
    const client: AnalysisClient = {
      startAnalysis: vi.fn(async () => ({
        id: 'failed-job',
        status: 'failed' as const,
        error: 'Analysis could not complete because the research provider was temporarily unavailable. Please try again.',
      })),
      getAnalysis: vi.fn(),
    }

    render(<App client={client} />)
    await user.click(screen.getByRole('button', { name: /review vehicle/i }))

    expect(await screen.findByText(/analysis could not complete/i)).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /configuration analysis/i })).not.toBeInTheDocument()
  })
})

describe('hosted recorded and simulated experiences', () => {
  async function openMiata(user: ReturnType<typeof userEvent.setup>) {
    await user.click(screen.getAllByRole('button', { name: 'View recorded run' })[0])
    await screen.findByText('Real recorded run data')
  }

  it('updates welcome configuration and availability when selection changes', async () => {
    const user = userEvent.setup()
    render(<App hostedDemo />)
    await user.selectOptions(screen.getByRole('combobox'), 'charger-daytona')
    expect(screen.getByText(/2025 Dodge Charger Daytona · Scat Pack/)).toBeInTheDocument()
    expect(screen.getAllByText('Demo simulation available')).toHaveLength(2)
    expect(screen.queryByText(/2026 Mazda MX-5 Miata · Grand Touring/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'View recorded run' })).not.toBeInTheDocument()
  })

  it('never invokes the live client or fetch when opening a recording', async () => {
    const user = userEvent.setup()
    const client = fakeClient()
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    render(<App hostedDemo client={client} />)
    await openMiata(user)
    expect(client.startAnalysis).not.toHaveBeenCalled()
    expect(fetchSpy).not.toHaveBeenCalled()
    fetchSpy.mockRestore()
  })

  it('opens genuine Miata data and clears the stale report on vehicle or pipeline change', async () => {
    const user = userEvent.setup()
    render(<App hostedDemo />)
    await openMiata(user)
    expect(screen.getByText('gemini-3.6-flash')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /inspect horsepower evidence/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Hybrid' }))
    expect(screen.queryByText('Real recorded run data')).not.toBeInTheDocument()
    await openMiata(user)
    await user.selectOptions(screen.getByRole('combobox'), 'tesla-model-y')
    expect(screen.queryByText('Real recorded run data')).not.toBeInTheDocument()
  })

  it('shows recorded metadata, keyboard focus, Escape return and genuine source links', async () => {
    const user = userEvent.setup()
    render(<App hostedDemo />)
    await openMiata(user)
    const trigger = screen.getByRole('button', { name: 'Inspect run details' })
    await user.click(trigger)
    const details = screen.getByRole('dialog', { name: 'Run details' })
    expect(within(details).getByText('Recorded run')).toBeInTheDocument()
    expect(within(details).getByText('gemini-3.6-flash')).toBeInTheDocument()
    expect(within(details).getByText('01_miata_gt_auto_ground_truth.json')).toBeInTheDocument()
    expect(within(details).getByText('Started')).toBeInTheDocument()
    expect(within(details).getByText('Total tokens')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Close run details' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('button', { name: 'Close run details' })).toHaveFocus()
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
    await user.click(screen.getByRole('button', { name: /inspect horsepower evidence/i }))
    expect(within(screen.getByRole('complementary', { name: 'Fact evidence' })).getAllByRole('link', { name: /open source/i }).length).toBeGreaterThan(0)
    await user.click(screen.getByRole('button', { name: 'Close evidence inspector' }))
    expect(screen.getByText('Real recorded run data')).toBeInTheDocument()
  })

  it('preserves the real GR86 Hybrid failure without rendering a report', async () => {
    const user = userEvent.setup()
    render(<App hostedDemo />)
    await user.selectOptions(screen.getByRole('combobox'), 'gr86-base')
    await user.click(screen.getByRole('button', { name: 'Hybrid' }))
    expect(screen.getAllByText('Recorded run failed')).toHaveLength(2)
    await user.click(screen.getAllByRole('button', { name: 'View recorded run' })[0])
    expect(await screen.findByText(/Recorded run failed: phase_a_batch_1_deadline_exceeded/)).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Configuration-matched facts' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Inspect run details' }))
    expect(within(screen.getByRole('dialog')).getByText('failed')).toBeInTheDocument()
    expect(within(screen.getByRole('dialog')).getByText('phase_a_batch_1_deadline_exceeded')).toBeInTheDocument()
  })

  it('simulates missing recordings with progress, labels, sample evidence and no provider telemetry', async () => {
    const user = userEvent.setup()
    const client = fakeClient()
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    render(<App hostedDemo client={client} demoDelayMs={0} />)
    await user.selectOptions(screen.getByRole('combobox'), 'charger-daytona')
    await user.click(screen.getAllByRole('button', { name: 'Run demo analysis' })[0])
    expect(await screen.findByText('Simulated demo analysis')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Illustrative sample facts' })).toBeInTheDocument()
    expect(screen.getByText(/not a recorded model result. Values/)).toBeInTheDocument()
    expect(client.startAnalysis).not.toHaveBeenCalled()
    expect(fetchSpy).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: 'Inspect run details' }))
    const details = screen.getByRole('dialog')
    expect(within(details).getByText('Simulated demo run')).toBeInTheDocument()
    expect(within(details).getByText('Local animation duration (not provider latency)')).toBeInTheDocument()
    expect(within(details).getAllByText('Not measured — no provider')).toHaveLength(2)
    await user.click(screen.getByRole('button', { name: 'Close run details' }))
    await user.click(screen.getByRole('button', { name: /inspect horsepower evidence/i }))
    const evidence = screen.getByRole('complementary', { name: 'Fact evidence' })
    expect(within(evidence).getByText('Simulated demo evidence')).toBeInTheDocument()
    expect(within(evidence).queryByRole('link')).not.toBeInTheDocument()
    fetchSpy.mockRestore()
  })

  it('keeps simulation outside benchmarks and returns to the report', async () => {
    const user = userEvent.setup()
    render(<App hostedDemo demoDelayMs={0} />)
    await user.click(screen.getAllByRole('button', { name: 'Run demo analysis' })[0])
    await screen.findByRole('heading', { name: 'Illustrative sample facts' })
    await user.click(screen.getByRole('button', { name: 'Benchmark results' }))
    const panel = screen.getByRole('complementary', { name: 'Benchmark results' })
    expect(within(panel).getByText(/preserved evaluation runs only/)).toBeInTheDocument()
    expect(within(panel).getByText('Failed at 90s')).toBeInTheDocument()
    expect(within(panel).queryByText('Simulated demo analysis')).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Close benchmark results' }))
    expect(screen.getByRole('heading', { name: 'Illustrative sample facts' })).toBeInTheDocument()
  })

  it('supports the phone navigation controls and gives Run details an empty state', async () => {
    const user = userEvent.setup()
    render(<App hostedDemo />)
    await user.click(screen.getByRole('button', { name: 'Open navigation' }))
    await user.click(screen.getByRole('button', { name: 'Run details' }))
    expect(screen.getByRole('dialog')).toHaveTextContent('Choose Run demo analysis or View recorded run first')
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
