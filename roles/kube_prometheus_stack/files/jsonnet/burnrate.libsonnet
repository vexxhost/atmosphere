// SLO: 99.9% availability → error budget = 0.001
// Thresholds = error_budget × burn_rate_multiplier
{
  critical: { multiplier: 14.4, threshold: '0.0144', longWindow: '1h', shortWindow: '5m' },
  high: { multiplier: 6, threshold: '0.006', longWindow: '6h', shortWindow: '30m' },
  moderate: { multiplier: 3, threshold: '0.003', longWindow: '1d', shortWindow: '2h' },
  low: { multiplier: 1, threshold: '0.001', longWindow: '3d', shortWindow: '6h' },
}
