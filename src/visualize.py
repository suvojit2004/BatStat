#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Locate the CSV file
csv_path = os.path.expanduser('~/battery_history.csv')

def time_to_minutes(time_str):
    """Converts HH:MM:SS string to total minutes."""
    try:
        h, m, s = map(int, str(time_str).split(':'))
        return h * 60 + m + s / 60.0
    except Exception:
        return 0

def main():
    if not os.path.exists(csv_path):
        print(f"❌ Error: Could not find '{csv_path}'.")
        return

    print("📊 Loading advanced telemetry data...")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    # Filter strictly for Discharging phases
    df_discharge = df[df['Phase'] == 'Discharging'].copy()

    if df_discharge.empty:
        print("⚠️ No 'Discharging' phases found in the CSV yet.")
        return

    # Calculate advanced detailed metrics
    df_discharge['Runtime (Mins)'] = df_discharge['Runtime'].apply(time_to_minutes)
    df_discharge['Network (Mins)'] = df_discharge['Network'].apply(time_to_minutes)
    df_discharge['Total Drain (%)'] = df_discharge['Start (%)'] - df_discharge['End (%)']
    
    # Calculate Efficiency (Minutes of use per 1% of battery lost). Avoid division by zero.
    df_discharge['Efficiency (Min/%)'] = np.where(
        df_discharge['Total Drain (%)'] > 0, 
        df_discharge['Runtime (Mins)'] / df_discharge['Total Drain (%)'], 
        0
    )

    # -----------------------------------------
    # BUILD THE ADVANCED DARK DASHBOARD
    # -----------------------------------------
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(14, 9))
    fig.canvas.manager.set_window_title('BatStat: Advanced Telemetry Dashboard')
    fig.suptitle('BatStat: Hardware Telemetry & Discharge Analytics', fontsize=18, fontweight='bold', color='#00FFFF', y=0.96)

    # Plot 1: Session Durations (Area Chart)
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(df_discharge['Session No'], df_discharge['Runtime (Mins)'], color='#39FF14', marker='o', linewidth=2.5, label='Total Runtime')
    ax1.plot(df_discharge['Session No'], df_discharge['Network (Mins)'], color='#00BFFF', marker='s', linestyle='--', linewidth=1.5, label='Wi-Fi Active')
    ax1.fill_between(df_discharge['Session No'], df_discharge['Runtime (Mins)'], alpha=0.15, color='#39FF14')
    ax1.set_title('Session Durations', color='#CCCCCC', fontweight='bold')
    ax1.set_ylabel('Duration (Minutes)')
    ax1.grid(color='#333333', linestyle=':', alpha=0.7)
    ax1.legend(loc='upper left')

    # Plot 2: Total Drain Percentage (Bar Chart with Annotations)
    ax2 = plt.subplot(2, 2, 2)
    bars = ax2.bar(df_discharge['Session No'], df_discharge['Total Drain (%)'], color='#FF0055', alpha=0.85, width=0.5)
    ax2.set_title('Battery Capacity Drained', color='#CCCCCC', fontweight='bold')
    ax2.set_ylabel('Percentage Loss (%)')
    ax2.grid(color='#333333', linestyle=':', axis='y', alpha=0.7)
    ax2.set_ylim(0, max(df_discharge['Total Drain (%)'].max() * 1.2, 10)) # Scale Y axis dynamically
    
    # Auto-label the exact percentage on top of each bar
    for bar in bars:
        yval = bar.get_height()
        if yval > 0:
            ax2.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{int(yval)}%", ha='center', va='bottom', color='white', fontsize=10, fontweight='bold')

    # Plot 3: Hardware Efficiency (Scatter/Line Chart)
    ax3 = plt.subplot(2, 1, 2)
    ax3.plot(df_discharge['Session No'], df_discharge['Efficiency (Min/%)'], color='#FFD700', marker='D', linewidth=2.5, markersize=8)
    ax3.fill_between(df_discharge['Session No'], df_discharge['Efficiency (Min/%)'], alpha=0.1, color='#FFD700')
    ax3.set_title('Hardware Efficiency (Minutes of screen-on time per 1% battery drop)', color='#CCCCCC', fontweight='bold')
    ax3.set_xlabel('Session Number', fontsize=12)
    ax3.set_ylabel('Minutes per 1%', fontsize=12)
    ax3.grid(color='#333333', linestyle=':', alpha=0.7)
    
    # Ensure X-Axis ticks are whole numbers (Session 1, 2, 3...) across all graphs
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.get_major_locator().set_params(integer=True)

    plt.tight_layout(pad=2.0)
    
    print("✨ Launching Advanced Telemetry Dashboard...")
    plt.show()

if __name__ == "__main__":
    main()
