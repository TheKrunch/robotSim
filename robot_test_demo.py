#!/usr/bin/env python3
"""
Robot Simulator - Single Robot Testing Demo
Run this to test individual robot configurations
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from robotsim import calculate_theoretical_max_score

def demo_single_robot_testing():
    """Demonstrate single robot configuration testing"""

    print("=== FRC Robot Strategy Simulator - Single Robot Testing ===\n")

    # Test configurations
    test_configs = [
        {
            "name": "Optimal Shooter",
            "role": "shooter",
            "shoot_time": 1.0,
            "max_storage": 28,
            "reload_time": 4.0,
            "accuracy_bonus": 0.0
        },
        {
            "name": "Optimal Defender",
            "role": "defender",
            "shoot_time": 2.0,
            "max_storage": 18,
            "reload_time": 7.0,
            "accuracy_bonus": -0.3  # Penalty from opponent defender
        },
        {
            "name": "Optimal Passer",
            "role": "passer",
            "shoot_time": 2.0,
            "max_storage": 16,
            "reload_time": 3.0,
            "accuracy_bonus": 0.0
        },
        {
            "name": "Fast Shooter",
            "role": "shooter",
            "shoot_time": 0.5,
            "max_storage": 32,
            "reload_time": 5.0,
            "accuracy_bonus": 0.0
        },
        {
            "name": "Slow Accurate Shooter",
            "role": "shooter",
            "shoot_time": 2.0,
            "max_storage": 20,
            "reload_time": 8.0,
            "accuracy_bonus": 0.0
        }
    ]

    for config in test_configs:
        print(f"--- {config['name']} ---")
        results = calculate_theoretical_max_score(
            config["shoot_time"],
            config["max_storage"],
            config["reload_time"],
            config["role"],
            config["accuracy_bonus"]
        )

        print(f"Role: {config['role'].capitalize()}")
        print(f"Shoot Time: {config['shoot_time']:.1f}s")
        print(f"Max Storage: {config['max_storage']} balls")
        print(f"Reload Time: {config['reload_time']:.1f}s")
        print(f"Accuracy Bonus: {config['accuracy_bonus']:+.1f}")
        print()
        print(f"THEORETICAL MAXIMUM PERFORMANCE:")
        print(f"  Auto Period Score: {results['auto_score']} points")
        print(f"  Teleop Fuel Score: {results['fuel_score'] - results['auto_score']} points")
        print(f"  Climbing Score: {results['climb_score']} points")
        print(f"  Total Fuel Score: {results['fuel_score']} points")
        print(f"  Total Score: {results['total_score'] + results['climb_score']} points")
        print(f"  Shots Taken: {results['shots_taken']}")
        print(f"  Time Used: {results['time_used']:.1f} seconds")
        print(f"  Effective Accuracy: {results['effective_accuracy']:.1%}")
        print()

        # Calculate realistic performance
        base_accuracy = 0.85 + (config["shoot_time"] - 1.0) * 0.03
        base_accuracy = min(0.95, max(0.85, base_accuracy))
        realistic_accuracy = min(1.0, base_accuracy + config["accuracy_bonus"])

        realistic_score = int(results['total_score'] * realistic_accuracy)

        print(f"REALISTIC PERFORMANCE (with {realistic_accuracy:.1%} accuracy):")
        print(f"  Total Fuel Score: {realistic_score} points")
        print(f"  Total Score: {realistic_score + results['climb_score']} points")
        print(f"  Performance vs Theoretical: {(realistic_score + results['climb_score']) / (results['total_score'] + results['climb_score']):.1%}")
        print("-" * 60)
        print()

if __name__ == "__main__":
    demo_single_robot_testing()