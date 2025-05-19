from .time_based_energy import simulate_daily_energy
from .time_based_emissions import simulate_daily_emissions
from .time_based_cost import simulate_daily_cost

def run_simulation(vehicle,
                   start_date,
                   end_date,
                   daily_km,
                   driving_conditions='mixed',
                   energy_source='eu_avg',
                   use_recuperation=True,
                   urban_share=0.5):
    """
    Собирает три симуляции в один список:
      [{'date':…, 'energy':{…}, 'co2_g':…, 'cost_rub':…}, …]
    """
    e = simulate_daily_energy(vehicle, start_date, end_date, daily_km, driving_conditions)
    em = simulate_daily_emissions(vehicle, start_date, end_date, daily_km,
                                  energy_source, driving_conditions,
                                  use_recuperation, urban_share)
    c = simulate_daily_cost(vehicle, start_date, end_date, daily_km, driving_conditions)

    combined = []
    for ener, emis, cost in zip(e, em, c):
        combined.append({
            'date':    ener['date'],
            'energy':  ener,
            'co2_g':   emis['co2_g'],
            'cost_rub':cost['cost_rub'],
        })
    return combined