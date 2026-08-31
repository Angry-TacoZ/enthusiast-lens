import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { App } from './App'

describe('standalone judge UI', () => {
  it('loads a canonical recorded result and opens its evidence inspector', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /open recorded analysis/i }))

    expect(await screen.findByRole('heading', { name: /2026 mazda mx-5 miata/i })).toBeInTheDocument()
    expect(screen.getByText('19/20')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /inspect horsepower evidence/i }))
    const inspector = screen.getByRole('complementary', { name: /fact evidence/i })
    expect(within(inspector).getByRole('heading', { name: 'Horsepower' })).toBeInTheDocument()
    expect(within(inspector).getByText('181 hp')).toBeInTheDocument()
    expect(within(inspector).getByRole('link', { name: /open source/i })).toHaveAttribute(
      'href',
      'https://www.mazdausa.com/vehicles/mx-5-miata',
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
    await user.click(screen.getByRole('button', { name: /load recorded run/i }))

    expect(await screen.findByRole('heading', { name: /hybrid result pending/i })).toBeInTheDocument()
    expect(screen.queryByText(/correct enthusiast fact coverage/i)).not.toBeInTheDocument()
  })
})
