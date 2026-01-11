import random
import csv
import os
total_time = 180
auto_time = 15
transition_shift_time = 20
aliance_shift_one_time = 30
aliance_shift_two_time = 55
alaince_shift_three_time = 80
alaince_shift_four_time = 105
end_game_time = 130

blue_hub_active_first = True

class robot:
    def __init__(self, name: str, current_storage: int, max_storage: int, shoot_time: float, reload_time: float, accuracy: float, can_auto_climb: bool, auto_climb_time: float, climb_level: int, climb_time: float, team: str, role: str = "shooter"):
        self.name = name
        self.current_storage = current_storage
        self.max_storage = max_storage
        self.shoot_time = shoot_time
        self.reload_time = reload_time
        self.accuracy = accuracy
        self.can_auto_climb = can_auto_climb
        self.auto_climb_time = auto_climb_time
        self.climb_level = climb_level
        self.climb_time = climb_time
        self.team = team
        self.role = role  # "shooter", "defender", "passer"
        
        self.scored = 0
        self.shots = 0
        self.reloads = 0
        self.time = 0
        self.has_climbed = False
        
        # Advanced stats tracking
        self.defensive_points = 0  # Points prevented from opponent due to defense
        self.offensive_points = 0   # Points contributed to team due to passing/reloading
        self.team_bonuses_provided = 0  # How much this robot's presence helps team bonuses
        
        # Scoreboard tracking
        self.scoring_events = []  # List of (time, points_scored) tuples
    
    def reset(self):
        self.scored = 0
        self.shots = 0
        self.reloads = 0
        self.time = 0
        self.has_climbed = False
        self.current_storage = self.max_storage
        
        # Reset advanced stats
        self.defensive_points = 0
        self.offensive_points = 0
        self.team_bonuses_provided = 0
        
        # Reset scoreboard tracking
        self.scoring_events = []

    def get_time(self):
        return self.time

    def get_name(self):
        return self.name

    def shoot(self, accuracy_bonus=0):
        if self.current_storage > 0:
            self.current_storage -= 1
            self.shots += 1
            self.time += self.shoot_time

            # Accuracy increases with shoot time (slower = more accurate)
            # Base accuracy ranges from 0.85 (fast shooting) to 0.95 (slow shooting)
            base_accuracy = 0.95 + (self.shoot_time - 1.0) * 0.03  # 0.03 accuracy per second
            base_accuracy = min(0.99, max(0.9, base_accuracy))  # Clamp between 0.85 and 0.95
            
            effective_accuracy = min(1.0, base_accuracy + accuracy_bonus)
            random_value = random.uniform(0, 1)
            if random_value <= effective_accuracy:
                self.scored += 1
                self.scoring_events.append((self.time, 1))  # Record scoring event
                # print(f"{self.name} made the shot!")
            else:
                # print(f"{self.name} missed the shot.")
                pass
        else:
            # print(f"{self.name} has no storage left to shoot.")
            return False
        return True
        
    def reload(self, reload_bonus=0):
        self.reloads += 1
        # During auto, max storage is 8 for all robots
        effective_max = 8 if self.time < auto_time else self.max_storage
        # Reload time scales with storage capacity
        reload_multiplier = effective_max / 8.0
        effective_reload = max(5.0, (self.reload_time - reload_bonus) * reload_multiplier)
        self.time += effective_reload
        self.current_storage = effective_max
        # print(f"{self.name} reloaded.")

    def defend(self):
        # Spend time defending, which debuffs opponents
        defense_time = 3.0  # Time spent defending
        self.time += defense_time
        # print(f"{self.name} played defense.")

    def pass_fuel(self):
        # Pass fuel to teammates, but for simplicity, just reload faster for self or something
        # Actually, passing is handled in team bonuses
        self.reload()  # For now, same as reload

    def auto_climb(self):
        if not self.can_auto_climb or self.has_climbed:
            # print(f"{self.name} cannot perform an automatic climb.")
            return False
            
        self.time += self.auto_climb_time
        self.has_climbed = True
        # print(f"{self.name} performed an automatic climb.")
        return True

    def climb(self):
        if self.climb_level == 0 or self.has_climbed:
            # print(f"{self.name} cannot climb.")
            return False
        
        self.time += self.climb_time
        self.has_climbed = True
        # print(f"{self.name} climbed to level {self.climb_level}.")
        return True
    
# Calculate team bonuses
def calculate_bonuses(robots):
    red_robots = [bot for bot in robots if bot.team == "Red"]
    blue_robots = [bot for bot in robots if bot.team == "Blue"]
    
    red_has_defender = any(bot.role == "defender" for bot in red_robots)
    red_has_passer = any(bot.role == "passer" for bot in red_robots)
    blue_has_defender = any(bot.role == "defender" for bot in blue_robots)
    blue_has_passer = any(bot.role == "passer" for bot in blue_robots)
    
    # Bonuses
    red_accuracy_bonus = -0.3 if blue_has_defender else 0
    red_reload_bonus = 1.5 if red_has_passer else 0
    blue_accuracy_bonus = -0.3 if red_has_defender else 0
    blue_reload_bonus = 1.5 if blue_has_passer else 0
    
    return {
        "red_accuracy_bonus": red_accuracy_bonus,
        "red_reload_bonus": red_reload_bonus,
        "blue_accuracy_bonus": blue_accuracy_bonus,
        "blue_reload_bonus": blue_reload_bonus
    }

def calculate_advanced_stats(robots, num_sims=50):
    """Calculate advanced stats showing defensive/offensive impact of each robot"""
    
    red_robots = [bot for bot in robots if bot.team == "Red"]
    blue_robots = [bot for bot in robots if bot.team == "Blue"]
    
    # Create baseline teams (all shooters)
    red_baseline = [create_robot(f"Red Baseline {i+1}", "Red", "shooter") for i in range(len(red_robots))]
    blue_baseline = [create_robot(f"Blue Baseline {i+1}", "Blue", "shooter") for i in range(len(blue_robots))]
    
    stats = {}
    
    # Test each robot's impact
    for robot in robots:
        if robot.role in ["defender", "passer"]:
            team = robot.team
            opponent_team = "Blue" if team == "Red" else "Red"
            
            # Create team with this robot
            test_team = []
            opp_team = []
            
            if team == "Red":
                test_team = [robot if r.name == robot.name else create_robot(r.name, r.team, r.role) 
                           for r in red_robots]
                opp_team = blue_baseline.copy()
            else:
                test_team = [robot if r.name == robot.name else create_robot(r.name, r.team, r.role) 
                           for r in blue_robots]
                opp_team = red_baseline.copy()
            
            test_robots = test_team + opp_team
            
            # Simulate with this robot
            test_scores = []
            for _ in range(num_sims):
                bonuses = calculate_bonuses(test_robots)
                r_score, b_score, _, _, _, _ = run_simulation(test_robots, bonuses, verbose=False)
                test_scores.append((r_score, b_score))
            
            # Simulate without this robot (replace with shooter)
            replacement = create_robot(f"Replacement {robot.name}", robot.team, "shooter")
            if team == "Red":
                no_special_team = [replacement if r.name == robot.name else r for r in test_team]
            else:
                no_special_team = [replacement if r.name == robot.name else r for r in test_team]
            
            no_special_robots = no_special_team + opp_team
            
            # Simulate without this robot
            baseline_scores = []
            for _ in range(num_sims):
                bonuses = calculate_bonuses(no_special_robots)
                r_score, b_score, _, _, _, _ = run_simulation(no_special_robots, bonuses, verbose=False)
                baseline_scores.append((r_score, b_score))
            
            # Calculate impact
            test_team_avg = sum(r if team == "Red" else b for r, b in test_scores) / len(test_scores)
            baseline_team_avg = sum(r if team == "Red" else b for r, b in baseline_scores) / len(baseline_scores)
            
            test_opp_avg = sum(b if team == "Red" else r for r, b in test_scores) / len(test_scores)
            baseline_opp_avg = sum(b if team == "Red" else r for r, b in baseline_scores) / len(baseline_scores)
            
            offensive_impact = test_team_avg - baseline_team_avg  # How much this robot helps their team
            defensive_impact = baseline_opp_avg - test_opp_avg    # How much this robot hurts the opponent
            
            stats[robot.name] = {
                "role": robot.role,
                "team": team,
                "offensive_points": offensive_impact,
                "defensive_points": defensive_impact,
                "net_impact": offensive_impact + defensive_impact,
                "win_rate_with": sum(1 for r, b in test_scores if (team == "Red" and r > b) or (team == "Blue" and b > r)) / len(test_scores) * 100,
                "win_rate_without": sum(1 for r, b in baseline_scores if (team == "Red" and r > b) or (team == "Blue" and b > r)) / len(baseline_scores) * 100
            }
    
    return stats

def display_scoreboard(robots):
    """Display a scoreboard showing when each robot scored during the match"""
    
    print("\n--- Match Scoreboard ---")
    print("Time | Robot | Team | Points | Cumulative Score")
    print("-" * 55)
    
    # Collect all scoring events across all robots
    all_events = []
    for bot in robots:
        for time_stamp, points in bot.scoring_events:
            all_events.append((time_stamp, bot.name, bot.team, points, bot.role))
    
    # Sort events by time
    all_events.sort(key=lambda x: x[0])
    
    # Track cumulative scores
    team_scores = {"Red": 0, "Blue": 0}
    robot_scores = {bot.name: 0 for bot in robots}
    
    for time_stamp, robot_name, team, points, role in all_events:
        # Update scores
        team_scores[team] += points
        robot_scores[robot_name] += points
        
        # Format time as MM:SS
        minutes = int(time_stamp // 60)
        seconds = time_stamp % 60
        time_str = f"{minutes}:{seconds:05.2f}"
        
        # Display event
        print(f"{time_str} | {robot_name} ({role}) | {team} | +{points} | {robot_scores[robot_name]} ({team_scores[team]})")
    
    print("-" * 55)
    print(f"Final Scores - Red: {team_scores['Red']}, Blue: {team_scores['Blue']}")
    
    # Show robot summaries
    print("\nRobot Performance Summary:")
    print("Robot | Role | Team | Total Scored | Shots Taken | Accuracy")
    print("-" * 65)
    
    for bot in robots:
        accuracy = bot.scored / bot.shots if bot.shots > 0 else 0
        print(f"{bot.name} | {bot.role} | {bot.team} | {bot.scored} | {bot.shots} | {accuracy:.1%}")

def calculate_theoretical_max_score(shoot_time, max_storage, reload_time, role="shooter", accuracy_bonus=0):
    """
    Calculate the theoretical maximum score a robot could achieve under ideal conditions.
    Assumes perfect accuracy, optimal timing, and no interruptions.
    """
    
    # Base accuracy calculation (same as in shoot method)
    base_accuracy = 0.85 + (shoot_time - 1.0) * 0.03
    base_accuracy = min(0.95, max(0.85, base_accuracy))
    effective_accuracy = min(1.0, base_accuracy + accuracy_bonus)
    
    # For theoretical max, assume perfect accuracy
    effective_accuracy = 1.0
    
    # Calculate time phases
    auto_period = 15  # seconds
    teleop_period = 135  # seconds (total 180 - 15 auto - 30 endgame)
    endgame_period = 30  # seconds
    
    total_score = 0
    total_time_used = 0
    
    # AUTO period (only shooting allowed, limited time)
    auto_shots_possible = min(max_storage, int(auto_period / shoot_time))
    auto_score = auto_shots_possible * effective_accuracy
    total_score += auto_score
    total_time_used += auto_shots_possible * shoot_time
    
    # Remaining storage after auto
    remaining_storage = max_storage - auto_shots_possible
    
    # TELEOP period (shooting + reloading)
    teleop_time_left = teleop_period
    
    # Calculate shooting cycles in teleop
    while teleop_time_left > 0 and remaining_storage > 0:
        # Shoot all remaining balls
        shots_this_cycle = min(remaining_storage, int(teleop_time_left / shoot_time))
        if shots_this_cycle == 0:
            break
            
        score_this_cycle = shots_this_cycle * effective_accuracy
        total_score += score_this_cycle
        time_for_shooting = shots_this_cycle * shoot_time
        
        # Reload if we have time and storage isn't full
        if remaining_storage - shots_this_cycle < max_storage and teleop_time_left - time_for_shooting > reload_time:
            time_for_shooting += reload_time
            remaining_storage = max_storage  # Full reload
        else:
            remaining_storage -= shots_this_cycle
        
        teleop_time_left -= time_for_shooting
    
    # ENDGAME climbing bonus
    climb_points = 0
    if role == "shooter":
        climb_points = 15  # Auto climb
    elif role == "defender":
        climb_points = 10  # Level 2 climb
    elif role == "passer":
        climb_points = 5   # Level 1 climb
    
    return {
        "total_score": int(total_score),
        "fuel_score": int(total_score),
        "climb_score": climb_points,
        "auto_score": int(auto_score),
        "shots_taken": int(auto_shots_possible + (total_score - auto_score) / effective_accuracy),
        "time_used": total_time_used,
        "effective_accuracy": effective_accuracy
    }

def export_simulation_data_to_csv(filename="robot_simulation_results.csv"):
    """Export comprehensive simulation data to CSV"""
    
    # Create robots for testing
    robots = [
        create_robot("Normal Robot 1", "Red", "shooter"),
        create_robot("Normal Robot 2", "Red", "shooter"),
        create_robot("Passer Robot", "Red", "passer"),
        create_robot("Fast Robot 1", "Blue", "shooter"),
        create_robot("Fast Robot 2", "Blue", "shooter"),
        create_robot("Defender Robot", "Blue", "defender")
    ]
    
    bonuses = calculate_bonuses(robots)
    
    # Run simulations to collect data
    print("Running simulations for CSV export...")
    
    # Advanced stats
    advanced_stats = calculate_advanced_stats(robots, num_sims=10)  # Reduced from 30
    
    # Parameter optimization data
    param_optimization_data = []
    
    # Test different shoot times
    for st in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]:
        for rt in [5.0, 6.0, 7.0, 8.0, 9.0, 10.0]:
            for ms in [8, 12, 16, 20, 24, 28, 32, 36]:
                score = test_robot_config(st, rt, ms, num_sims=5)  # Reduced from 10
                param_optimization_data.append({
                    "shoot_time": st,
                    "reload_time": rt,
                    "max_storage": ms,
                    "avg_score": score
                })
    
    # Team composition data
    team_composition_data = []
    compositions = [
        (["shooter", "shooter", "shooter"], ["shooter", "shooter", "shooter"]),
        (["shooter", "shooter", "defender"], ["shooter", "shooter", "shooter"]),
        (["shooter", "shooter", "passer"], ["shooter", "shooter", "shooter"]),
        (["shooter", "defender", "passer"], ["shooter", "shooter", "shooter"]),
        (["defender", "defender", "defender"], ["shooter", "shooter", "shooter"]),
        (["passer", "passer", "passer"], ["shooter", "shooter", "shooter"]),
        (["shooter", "shooter", "shooter"], ["shooter", "shooter", "defender"]),
        (["shooter", "shooter", "shooter"], ["shooter", "shooter", "passer"])
    ]
    
    for red_comp, blue_comp in compositions:
        avg_red, avg_blue, win_rate = test_team_composition(red_comp, blue_comp, num_sims=10)  # Reduced from 20
        team_composition_data.append({
            "red_composition": str(red_comp),
            "blue_composition": str(blue_comp),
            "red_avg_score": avg_red,
            "blue_avg_score": avg_blue,
            "red_win_rate": win_rate
        })
    
    # Role optimization data
    role_data = []
    roles = ["shooter", "defender", "passer"]
    for role in roles:
        config, score = optimize_role(role, num_sims=8)  # Reduced from 15
        shoot_time, max_storage, reload_time = config
        accuracy = 0.85 + (shoot_time - 1.0) * 0.03
        accuracy = min(0.95, max(0.85, accuracy))
        role_data.append({
            "role": role,
            "optimal_shoot_time": shoot_time,
            "optimal_max_storage": max_storage,
            "optimal_reload_time": reload_time,
            "optimal_accuracy": accuracy,
            "optimal_score": score
        })
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(["Data Type", "Category", "Subcategory", "Value 1", "Value 2", "Value 3", "Value 4", "Value 5"])
        
        # Advanced stats
        writer.writerow(["Advanced Stats", "Header", "", "", "", "", ""])
        for robot_name, stats in advanced_stats.items():
            writer.writerow([
                "Advanced Stats", "Robot Impact", robot_name,
                f"Offensive: {stats['offensive_points']:+.1f}",
                f"Defensive: {stats['defensive_points']:+.1f}",
                f"Net: {stats['net_impact']:+.1f}",
                f"Win Rate: {stats['win_rate_with']:.1f}%"
            ])
        
        # Parameter optimization
        writer.writerow([])
        writer.writerow(["Parameter Optimization", "Header", "", "", "", "", ""])
        for data in param_optimization_data:
            writer.writerow([
                "Parameter Optimization", "Configuration", "",
                f"Shoot: {data['shoot_time']:.1f}s",
                f"Reload: {data['reload_time']:.1f}s",
                f"Storage: {data['max_storage']}",
                f"Score: {data['avg_score']:.1f}"
            ])
        
        # Team composition
        writer.writerow([])
        writer.writerow(["Team Composition", "Header", "", "", "", "", ""])
        for data in team_composition_data:
            writer.writerow([
                "Team Composition", "Matchup", "",
                data['red_composition'],
                data['blue_composition'],
                f"Red Score: {data['red_avg_score']:.1f}",
                f"Win Rate: {data['red_win_rate']:.1f}%"
            ])
        
        # Role optimization
        writer.writerow([])
        writer.writerow(["Role Optimization", "Header", "", "", "", "", ""])
        for data in role_data:
            writer.writerow([
                "Role Optimization", data['role'], "",
                f"Shoot: {data['optimal_shoot_time']:.1f}s",
                f"Storage: {data['optimal_max_storage']}",
                f"Reload: {data['optimal_reload_time']:.1f}s",
                f"Score: {data['optimal_score']:.1f}"
            ])
    
    print(f"Simulation data exported to {filename}")

def test_single_robot_stats():
    """Interactive function to test single robot configurations"""
    print("\n--- Single Robot Stats Tester ---")
    print("Enter robot parameters to calculate theoretical maximum performance:")
    
    try:
        role = input("Role (shooter/defender/passer) [shooter]: ").strip().lower() or "shooter"
        if role not in ["shooter", "defender", "passer"]:
            print("Invalid role. Using 'shooter'.")
            role = "shooter"
        
        shoot_time = float(input("Shoot time (seconds) [1.5]: ").strip() or "1.5")
        max_storage = int(input("Max storage capacity [16]: ").strip() or "16")
        reload_time = float(input("Reload time (seconds) [5.0]: ").strip() or "5.0")
        accuracy_bonus = float(input("Accuracy bonus [-0.3 to 0.0] [0.0]: ").strip() or "0.0")
        
        # Calculate theoretical max
        results = calculate_theoretical_max_score(shoot_time, max_storage, reload_time, role, accuracy_bonus)
        
        print(f"\n--- Theoretical Maximum Performance for {role.capitalize()} ---")
        print(f"Parameters: Shoot {shoot_time:.1f}s, Storage {max_storage}, Reload {reload_time:.1f}s")
        print(f"Accuracy Bonus: {accuracy_bonus:+.1f}")
        print(f"Effective Accuracy: {results['effective_accuracy']:.1%}")
        print()
        print(f"Auto Period Score: {results['auto_score']} points")
        print(f"Teleop Fuel Score: {results['fuel_score'] - results['auto_score']} points")
        print(f"Climbing Score: {results['climb_score']} points")
        print(f"Total Fuel Score: {results['fuel_score']} points")
        print(f"Total Score: {results['total_score'] + results['climb_score']} points")
        print(f"Shots Taken: {results['shots_taken']}")
        print(f"Time Used: {results['time_used']:.1f} seconds")
        print(f"Time Efficiency: {(results['total_score'] + results['climb_score']) / 180:.1%} of available time")
        
        # Calculate realistic performance (with actual accuracy)
        base_accuracy = 0.85 + (shoot_time - 1.0) * 0.03
        base_accuracy = min(0.95, max(0.85, base_accuracy))
        realistic_accuracy = min(1.0, base_accuracy + accuracy_bonus)
        
        realistic_results = calculate_theoretical_max_score(shoot_time, max_storage, reload_time, role, accuracy_bonus)
        realistic_results['effective_accuracy'] = realistic_accuracy
        realistic_results['total_score'] = int(results['total_score'] * realistic_accuracy)
        realistic_results['fuel_score'] = realistic_results['total_score']
        realistic_results['auto_score'] = int(results['auto_score'] * realistic_accuracy)
        
        print(f"\n--- Realistic Performance (with {realistic_accuracy:.1%} accuracy) ---")
        print(f"Total Fuel Score: {realistic_results['fuel_score']} points")
        print(f"Total Score: {realistic_results['fuel_score'] + results['climb_score']} points")
        
    except ValueError as e:
        print(f"Invalid input: {e}")
    except KeyboardInterrupt:
        print("\nTest cancelled.")

def run_simulation(robots, bonuses, verbose=False):
    # Reset robots
    for bot in robots:
        bot.reset()
    
    # Simulate AUTO period
    if verbose: print("Starting AUTO period...")
    for bot in robots:
        while bot.time < auto_time and bot.time < total_time:
            if bot.role == "shooter":
                if bot.current_storage > 0:
                    accuracy_bonus = bonuses[f"{bot.team.lower()}_accuracy_bonus"]
                    bot.shoot(accuracy_bonus)
                elif bot.can_auto_climb and not bot.has_climbed and bot.time + bot.auto_climb_time <= auto_time:
                    bot.auto_climb()
                else:
                    break
            elif bot.role == "defender":
                # Defender can defend or shoot occasionally
                if random.random() < 0.5 and bot.current_storage > 0:
                    accuracy_bonus = bonuses[f"{bot.team.lower()}_accuracy_bonus"]
                    bot.shoot(accuracy_bonus)
                else:
                    bot.defend()
            elif bot.role == "passer":
                if bot.current_storage > 0:
                    accuracy_bonus = bonuses[f"{bot.team.lower()}_accuracy_bonus"]
                    bot.shoot(accuracy_bonus)
                else:
                    reload_bonus = bonuses[f"{bot.team.lower()}_reload_bonus"]
                    bot.reload(reload_bonus)

    # Calculate auto scores
    red_auto = sum(bot.scored for bot in robots if bot.team == "Red")
    blue_auto = sum(bot.scored for bot in robots if bot.team == "Blue")
    if verbose: print(f"Red auto fuel: {red_auto}")
    if verbose: print(f"Blue auto fuel: {blue_auto}")

    # Determine hub inactive order
    if red_auto > blue_auto:
        inactive_team = "Red"
    elif blue_auto > red_auto:
        inactive_team = "Blue"
    else:
        inactive_team = random.choice(["Red", "Blue"])

    if verbose: print(f"First inactive hub in shifts: {inactive_team}")

    def is_hub_active(team, time):
        if time < transition_shift_time:
            return True  # AUTO and TRANSITION
        elif time >= end_game_time:
            return True  # END GAME
        else:
            # ALLIANCE SHIFTS
            shifts = [
                (aliance_shift_one_time, aliance_shift_two_time),
                (aliance_shift_two_time, alaince_shift_three_time),
                (alaince_shift_three_time, alaince_shift_four_time),
                (alaince_shift_four_time, end_game_time)
            ]
            for i, (start, end) in enumerate(shifts):
                if start <= time < end:
                    if i % 2 == 0:
                        inactive = inactive_team
                    else:
                        inactive = "Blue" if inactive_team == "Red" else "Red"
                    return team != inactive
            return True  # Should not reach here

    # Simulate TRANSITION and ALLIANCE SHIFTS
    if verbose: print("Starting TRANSITION and ALLIANCE SHIFTS...")
    for bot in robots:
        while bot.time < end_game_time and bot.time < total_time:
            if bot.role == "shooter":
                if is_hub_active(bot.team, bot.time):
                    if bot.current_storage > 0:
                        accuracy_bonus = bonuses[f"{bot.team.lower()}_accuracy_bonus"]
                        bot.shoot(accuracy_bonus)
                    else:
                        reload_bonus = bonuses[f"{bot.team.lower()}_reload_bonus"]
                        bot.reload(reload_bonus)
                else:
                    reload_bonus = bonuses[f"{bot.team.lower()}_reload_bonus"]
                    bot.reload(reload_bonus)
            elif bot.role == "defender":
                if random.random() < 0.3:  # Occasionally shoot
                    if is_hub_active(bot.team, bot.time) and bot.current_storage > 0:
                        accuracy_bonus = bonuses[f"{bot.team.lower()}_accuracy_bonus"]
                        bot.shoot(accuracy_bonus)
                    else:
                        reload_bonus = bonuses[f"{bot.team.lower()}_reload_bonus"]
                        bot.reload(reload_bonus)
                else:
                    bot.defend()
            elif bot.role == "passer":
                if is_hub_active(bot.team, bot.time):
                    if bot.current_storage > 0:
                        accuracy_bonus = bonuses[f"{bot.team.lower()}_accuracy_bonus"]
                        bot.shoot(accuracy_bonus)
                    else:
                        reload_bonus = bonuses[f"{bot.team.lower()}_reload_bonus"]
                        bot.reload(reload_bonus)
                else:
                    reload_bonus = bonuses[f"{bot.team.lower()}_reload_bonus"]
                    bot.reload(reload_bonus)

    # Simulate END GAME
    if verbose: print("Starting END GAME...")
    for bot in robots:
        while bot.time < total_time:
            if not bot.has_climbed and bot.climb_level > 0 and bot.time + bot.climb_time <= total_time:
                bot.climb()
            else:
                break

    # Calculate scores
    red_fuel = sum(bot.scored for bot in robots if bot.team == "Red")
    blue_fuel = sum(bot.scored for bot in robots if bot.team == "Blue")

    red_climb = 0
    blue_climb = 0
    for bot in robots:
        if bot.has_climbed:
            if bot.team == "Red":
                if bot.can_auto_climb and bot.auto_climb_time > 0:
                    red_climb += 15
                else:
                    red_climb += bot.climb_level * 10
            else:
                if bot.can_auto_climb and bot.auto_climb_time > 0:
                    blue_climb += 15
                else:
                    blue_climb += bot.climb_level * 10

    red_score = red_fuel + red_climb
    blue_score = blue_fuel + blue_climb

    return red_score, blue_score, red_fuel, blue_fuel, red_climb, blue_climb

def create_robot(name, team, role, shoot_time=None, max_storage=None, reload_time=None, can_auto_climb=None, auto_climb_time=None, climb_level=None, climb_time=None):
    """Create a robot with role-appropriate default stats"""
    
    # Role-based defaults
    if role == "shooter":
        # Fast shooting, good accuracy from speed
        default_shoot_time = 1.5
        default_max_storage = 16
        default_reload_time = 5.0
        default_can_auto_climb = True
        default_auto_climb_time = 5.0
        default_climb_level = 2
        default_climb_time = 10.0
    elif role == "defender":
        # Slower shooting (worse shooter), focused on defense
        default_shoot_time = 3.0  # Slower = less effective shooter
        default_max_storage = 8
        default_reload_time = 6.0
        default_can_auto_climb = False
        default_auto_climb_time = 0
        default_climb_level = 2
        default_climb_time = 10.0
    elif role == "passer":
        # Medium shooting speed, good at passing/reloading
        default_shoot_time = 2.5  # Medium speed
        default_max_storage = 20
        default_reload_time = 4.0
        default_can_auto_climb = False
        default_auto_climb_time = 0
        default_climb_level = 1
        default_climb_time = 8.0
    else:
        raise ValueError(f"Unknown role: {role}")
    
    # Use provided values or defaults
    shoot_time = shoot_time if shoot_time is not None else default_shoot_time
    max_storage = max_storage if max_storage is not None else default_max_storage
    reload_time = reload_time if reload_time is not None else default_reload_time
    can_auto_climb = can_auto_climb if can_auto_climb is not None else default_can_auto_climb
    auto_climb_time = auto_climb_time if auto_climb_time is not None else default_auto_climb_time
    climb_level = climb_level if climb_level is not None else default_climb_level
    climb_time = climb_time if climb_time is not None else default_climb_time
    
    return robot(name, 8, max_storage, shoot_time, reload_time, 0.8, can_auto_climb, auto_climb_time, climb_level, climb_time, team, role)

# Create robots with different strategies
# Red team: mix of shooters and a passer
normal_robot1 = create_robot("Normal Robot 1", "Red", "shooter")
normal_robot2 = create_robot("Normal Robot 2", "Red", "shooter")
passer_robot = create_robot("Passer Robot", "Red", "passer")

# Blue team: fast shooters and a defender
fast_robot1 = create_robot("Fast Robot 1", "Blue", "shooter")
fast_robot2 = create_robot("Fast Robot 2", "Blue", "shooter")
defender_robot = create_robot("Defender Robot", "Blue", "defender")

robots = [normal_robot1, normal_robot2, passer_robot, fast_robot1, fast_robot2, defender_robot]

bonuses = calculate_bonuses(robots)
print(f"Team Bonuses: {bonuses}")

# Run multiple simulations
num_simulations = 100
red_scores = []
blue_scores = []
red_fuel_scores = []
blue_fuel_scores = []
red_climb_scores = []
blue_climb_scores = []
red_wins = 0
blue_wins = 0
ties = 0

for sim in range(num_simulations):
    r_score, b_score, r_fuel, b_fuel, r_climb, b_climb = run_simulation(robots, bonuses, verbose=False)
    red_scores.append(r_score)
    blue_scores.append(b_score)
    red_fuel_scores.append(r_fuel)
    blue_fuel_scores.append(b_fuel)
    red_climb_scores.append(r_climb)
    blue_climb_scores.append(b_climb)
    if r_score > b_score:
        red_wins += 1
    elif b_score > r_score:
        blue_wins += 1
    else:
        ties += 1

# Calculate averages
avg_red_score = sum(red_scores) / num_simulations
avg_blue_score = sum(blue_scores) / num_simulations
avg_red_fuel = sum(red_fuel_scores) / num_simulations
avg_blue_fuel = sum(blue_fuel_scores) / num_simulations
avg_red_climb = sum(red_climb_scores) / num_simulations
avg_blue_climb = sum(blue_climb_scores) / num_simulations

print(f"\nAfter {num_simulations} simulations:")
print(f"Red Team - Avg Fuel: {avg_red_fuel:.1f}, Avg Climb: {avg_red_climb:.1f}, Avg Total: {avg_red_score:.1f}")
print(f"Blue Team - Avg Fuel: {avg_blue_fuel:.1f}, Avg Climb: {avg_blue_climb:.1f}, Avg Total: {avg_blue_score:.1f}")
print(f"Win Rates - Red: {red_wins/num_simulations*100:.1f}%, Blue: {blue_wins/num_simulations*100:.1f}%, Ties: {ties/num_simulations*100:.1f}%")

# Calculate and display advanced stats
print("\n--- Advanced Stats: Defensive/Offensive Impact ---")
advanced_stats = calculate_advanced_stats(robots, num_sims=30)  # Use fewer sims for speed

for robot_name, stats in advanced_stats.items():
    print(f"\n{robot_name} ({stats['role']} on {stats['team']} Team):")
    print(f"  Offensive Impact: {stats['offensive_points']:+.1f} points (helps own team)")
    print(f"  Defensive Impact: {stats['defensive_points']:+.1f} points (hurts opponent)")
    print(f"  Net Impact: {stats['net_impact']:+.1f} points")
    print(f"  Win Rate With: {stats['win_rate_with']:.1f}% | Without: {stats['win_rate_without']:.1f}%")
    print(f"  Win Rate Change: {stats['win_rate_with'] - stats['win_rate_without']:+.1f}%")

# Run one simulation for the scoreboard (quiet) and one for verbose output
print("\n--- Sample Simulation ---")
red_score, blue_score, red_fuel, blue_fuel, red_climb, blue_climb = run_simulation(robots, bonuses, verbose=True)

# Display the scoreboard for this match
display_scoreboard(robots)

# Output stats for sample

# Output stats for sample
print("\nRobot Stats:")
for bot in robots:
    climb_type = "Auto" if bot.can_auto_climb and bot.auto_climb_time > 0 and bot.has_climbed else f"Level {bot.climb_level}" if bot.has_climbed else "None"
    print(f"{bot.name} ({bot.role}): Scored {bot.scored}, Shots {bot.shots}, Reloads {bot.reloads}, Climb {climb_type}, Final Time {bot.time:.1f}")

print(f"\nRed Team Fuel: {red_fuel}, Climb: {red_climb}, Total: {red_score}")
print(f"Blue Team Fuel: {blue_fuel}, Climb: {blue_climb}, Total: {blue_score}")

if red_score > blue_score:
    print("Red Team wins!")
elif blue_score > red_score:
    print("Blue Team wins!")
else:
    print("It's a tie!")

# Parameter optimization
print("\n--- Parameter Optimization ---")
print("Testing different robot configurations to find optimal shoot_time, reload_time, and max_storage")

def test_robot_config(shoot_time, reload_time, max_storage, num_sims=50):
    # Create test robots with given parameters
    test_robots = [
        robot(f"Test Robot {i+1}", 8, max_storage, shoot_time, reload_time, 1.0, True, 5.0, 2, 10.0, "Red", "shooter")
        for i in range(3)
    ] + [
        robot(f"Opponent {i+1}", 8, 8, 2.5, 5.0, 1.0, True, 5.0, 2, 10.0, "Blue", "shooter")
        for i in range(3)
    ]
    
    bonuses = calculate_bonuses(test_robots)
    scores = []
    
    for _ in range(num_sims):
        r_score, _, _, _, _, _ = run_simulation(test_robots, bonuses, verbose=False)
        scores.append(r_score)
    
    return sum(scores) / len(scores)

# Test different combinations
shoot_times = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
reload_times = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
max_storages = [8, 12, 16, 20, 24, 28, 32, 36]

best_score = 0
best_config = None

print("Testing configurations...")
for st in shoot_times:
    for rt in reload_times:
        for ms in max_storages:
            avg_score = test_robot_config(st, rt, ms)
            if avg_score > best_score:
                best_score = avg_score
                best_config = (st, rt, ms)
            print(f"Shoot: {st:.1f}s, Reload: {rt:.1f}s, Storage: {ms} -> Avg Score: {avg_score:.1f}")

print(f"\nBest Configuration: Shoot {best_config[0]:.1f}s, Reload {best_config[1]:.1f}s, Storage {best_config[2]} -> Avg Score: {best_score:.1f}")

# Analyze trade-offs
print("\n--- Trade-off Analysis ---")
print("Effect of shoot_time (fixed reload=5.0s, storage=24):")
for st in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
    score = test_robot_config(st, 5.0, 24)
    print(f"Shoot {st:.1f}s: {score:.1f}")

print("\nEffect of reload_time (fixed shoot=2.0s, storage=24):")
for rt in [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]:
    score = test_robot_config(2.0, rt, 24)
    print(f"Reload {rt:.1f}s: {score:.1f}")

print("\nEffect of max_storage (fixed shoot=2.0s, reload=5.0s):")
for ms in [8, 12, 16, 20, 24, 28, 32, 36, 40]:
    score = test_robot_config(2.0, 5.0, ms)
    print(f"Storage {ms}: {score:.1f}")

# Team composition optimization
print("\n--- Team Composition Optimization ---")
print("Testing different team makeups (3 robots per team)")

def test_team_composition(red_roles, blue_roles, num_sims=50):
    # Create test teams with given role compositions
    red_robots = []
    for i, role in enumerate(red_roles):
        red_robots.append(create_robot(f"Red {role} {i+1}", "Red", role))
    
    blue_robots = []
    for i, role in enumerate(blue_roles):
        blue_robots.append(create_robot(f"Blue {role} {i+1}", "Blue", role))
    
    test_robots = red_robots + blue_robots
    bonuses = calculate_bonuses(test_robots)
    red_scores = []
    blue_scores = []
    
    for _ in range(num_sims):
        r_score, b_score, _, _, _, _ = run_simulation(test_robots, bonuses, verbose=False)
        red_scores.append(r_score)
        blue_scores.append(b_score)
    
    avg_red = sum(red_scores) / len(red_scores)
    avg_blue = sum(blue_scores) / len(blue_scores)
    red_wins = sum(1 for r, b in zip(red_scores, blue_scores) if r > b)
    win_rate = red_wins / num_sims * 100
    
    return avg_red, avg_blue, win_rate

# Test different team compositions
compositions = [
    (["shooter", "shooter", "shooter"], ["shooter", "shooter", "shooter"]),  # All shooters
    (["shooter", "shooter", "defender"], ["shooter", "shooter", "shooter"]),  # 1 defender
    (["shooter", "shooter", "passer"], ["shooter", "shooter", "shooter"]),    # 1 passer
    (["shooter", "defender", "passer"], ["shooter", "shooter", "shooter"]),  # 1 each special
    (["defender", "defender", "defender"], ["shooter", "shooter", "shooter"]),  # All defenders
    (["passer", "passer", "passer"], ["shooter", "shooter", "shooter"]),      # All passers
    (["shooter", "shooter", "shooter"], ["shooter", "shooter", "defender"]), # Opponent has defender
    (["shooter", "shooter", "shooter"], ["shooter", "shooter", "passer"]),   # Opponent has passer
]

best_win_rate = 0
best_composition = None

print("Testing team compositions...")
for red_comp, blue_comp in compositions:
    avg_red, avg_blue, win_rate = test_team_composition(red_comp, blue_comp)
    comp_str = f"Red{red_comp} vs Blue{blue_comp}"
    print(f"{comp_str}: Red {avg_red:.1f}, Blue {avg_blue:.1f}, Win Rate {win_rate:.1f}%")
    if win_rate > best_win_rate:
        best_win_rate = win_rate
        best_composition = (red_comp, blue_comp)

print(f"\nBest Team Composition: Red{best_composition[0]} vs Blue{best_composition[1]} -> Red Team Win Rate {best_win_rate:.1f}%")

# Role optimization - find best stats for each role
print("\n--- Role Optimization ---")
print("Finding optimal stats for each robot role")

def optimize_role(role, num_sims=30):
    """Find the best stats for a given role by testing different configurations"""
    best_score = 0
    best_config = None
    
    # Test different shoot times (affects accuracy)
    shoot_times = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0] if role == "shooter" else [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    
    # Test different max storages
    max_storages = [8, 12, 16, 20, 24, 28, 32] if role == "shooter" else [6, 8, 10, 12, 14, 16, 18]
    
    # Test different reload times
    reload_times = [3.0, 4.0, 5.0, 6.0, 7.0, 8.0] if role == "passer" else [4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    
    print(f"Optimizing {role} role...")
    
    for shoot_time in shoot_times:
        for max_storage in max_storages:
            for reload_time in reload_times:
                # Create test robot with these stats
                test_robot = create_robot(f"Test {role}", "Red", role, 
                                        shoot_time=shoot_time, 
                                        max_storage=max_storage, 
                                        reload_time=reload_time)
                
                # Create opposing team of 3 shooters
                opp_robots = [create_robot(f"Opp {i+1}", "Blue", "shooter") for i in range(3)]
                test_robots = [test_robot] + opp_robots
                
                bonuses = calculate_bonuses(test_robots)
                scores = []
                
                for _ in range(num_sims):
                    r_score, b_score, _, _, _, _ = run_simulation(test_robots, bonuses, verbose=False)
                    scores.append(r_score)  # Test robot is on red team
                
                avg_score = sum(scores) / len(scores)
                
                if avg_score > best_score:
                    best_score = avg_score
                    best_config = (shoot_time, max_storage, reload_time)
    
    return best_config, best_score

# Optimize each role
roles = ["shooter", "defender", "passer"]
role_optimals = {}

for role in roles:
    config, score = optimize_role(role)
    role_optimals[role] = config
    shoot_time, max_storage, reload_time = config
    print(f"{role.capitalize()}: Shoot {shoot_time:.1f}s, Storage {max_storage}, Reload {reload_time:.1f}s -> Score {score:.1f}")

print("\n--- Most Effective Stats for Each Role ---")
for role, (shoot_time, max_storage, reload_time) in role_optimals.items():
    accuracy = 0.7 + (shoot_time - 1.0) * 0.05
    accuracy = min(0.95, max(0.7, accuracy))
    print(f"{role.capitalize()}:")
    print(f"  Shoot Time: {shoot_time:.1f}s (Accuracy: {accuracy:.2f})")
    print(f"  Max Storage: {max_storage} balls")
    print(f"  Reload Time: {reload_time:.1f}s")
    print()

# Export data to CSV
print("\n--- Exporting Data to CSV ---")
export_simulation_data_to_csv()

# Single robot testing
print("\n--- Single Robot Stats Testing ---")
print("Testing sample robot configurations...")

# Test a few sample configurations
test_configs = [
    {"role": "shooter", "shoot_time": 1.0, "max_storage": 28, "reload_time": 4.0, "accuracy_bonus": 0.0},
    {"role": "defender", "shoot_time": 2.0, "max_storage": 18, "reload_time": 7.0, "accuracy_bonus": -0.3},
    {"role": "passer", "shoot_time": 2.0, "max_storage": 16, "reload_time": 3.0, "accuracy_bonus": 0.0},
    {"role": "shooter", "shoot_time": 0.5, "max_storage": 32, "reload_time": 5.0, "accuracy_bonus": 0.0},  # Fast shooter
]

for i, config in enumerate(test_configs, 1):
    print(f"\n--- Test Configuration {i} ---")
    results = calculate_theoretical_max_score(
        config["shoot_time"], 
        config["max_storage"], 
        config["reload_time"], 
        config["role"], 
        config["accuracy_bonus"]
    )
    
    print(f"Role: {config['role'].capitalize()}")
    print(f"Parameters: Shoot {config['shoot_time']:.1f}s, Storage {config['max_storage']}, Reload {config['reload_time']:.1f}s")
    print(f"Accuracy Bonus: {config['accuracy_bonus']:+.1f}")
    print(f"Total Score: {results['total_score'] + results['climb_score']} points")
    print(f"Fuel Score: {results['fuel_score']} points")
    print(f"Climb Score: {results['climb_score']} points")
    print(f"Shots Taken: {results['shots_taken']}")
    print(f"Effective Accuracy: {results['effective_accuracy']:.1%}")

print("\n--- Interactive Testing ---")
print("To test custom configurations interactively, run test_single_robot_stats() in Python")
print("Example: test_single_robot_stats()")