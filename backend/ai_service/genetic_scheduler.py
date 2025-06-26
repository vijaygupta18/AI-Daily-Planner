import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import copy

class Task:
    """Represents a single task to be scheduled"""
    def __init__(self, task_id: str, name: str, duration: int, priority: int, 
                 deadline: Optional[datetime] = None, preferred_time: Optional[str] = None):
        self.id = task_id
        self.name = name
        self.duration = duration  # in minutes
        self.priority = priority  # 1-5, 5 being highest
        self.deadline = deadline
        self.preferred_time = preferred_time  # 'morning', 'afternoon', 'evening'
        self.completed = False

class TimeSlot:
    """Represents a time slot in the schedule"""
    def __init__(self, start_time: datetime, end_time: datetime, task: Optional[Task] = None):
        self.start_time = start_time
        self.end_time = end_time
        self.task = task
        self.is_break = False

class GeneticScheduler:
    """Genetic Algorithm-based scheduler for optimal task arrangement"""
    
    def __init__(self, work_start_hour: int = 8, work_end_hour: int = 20,
                 break_duration: int = 15, lunch_duration: int = 60):
        self.work_start_hour = work_start_hour
        self.work_end_hour = work_end_hour
        self.break_duration = break_duration
        self.lunch_duration = lunch_duration
        self.population_size = 100
        self.generations = 50
        self.mutation_rate = 0.1
        self.elite_size = 20
        
    def create_initial_population(self, tasks: List[Task], date: datetime) -> List[List[TimeSlot]]:
        """Generate initial population of schedules"""
        population = []
        
        for _ in range(self.population_size):
            schedule = self._create_random_schedule(tasks, date)
            population.append(schedule)
            
        return population
    
    def _create_random_schedule(self, tasks: List[Task], date: datetime) -> List[TimeSlot]:
        """Create a random valid schedule"""
        schedule = []
        work_start = date.replace(hour=self.work_start_hour, minute=0, second=0)
        work_end = date.replace(hour=self.work_end_hour, minute=0, second=0)
        
        # Shuffle tasks for randomness
        shuffled_tasks = tasks.copy()
        random.shuffle(shuffled_tasks)
        
        current_time = work_start
        
        # Add lunch break
        lunch_start = date.replace(hour=12, minute=0, second=0)
        lunch_slot = TimeSlot(lunch_start, lunch_start + timedelta(minutes=self.lunch_duration))
        lunch_slot.is_break = True
        
        for task in shuffled_tasks:
            # Skip lunch time
            if current_time <= lunch_start < current_time + timedelta(minutes=task.duration):
                current_time = lunch_start + timedelta(minutes=self.lunch_duration)
            
            # Check if task fits in remaining time
            if current_time + timedelta(minutes=task.duration) <= work_end:
                slot = TimeSlot(current_time, current_time + timedelta(minutes=task.duration), task)
                schedule.append(slot)
                current_time = slot.end_time
                
                # Add break after task (except last task)
                if current_time + timedelta(minutes=self.break_duration) < work_end:
                    break_slot = TimeSlot(current_time, current_time + timedelta(minutes=self.break_duration))
                    break_slot.is_break = True
                    schedule.append(break_slot)
                    current_time = break_slot.end_time
        
        # Insert lunch break at appropriate position
        schedule.append(lunch_slot)
        schedule.sort(key=lambda x: x.start_time)
        
        return schedule
    
    def fitness(self, schedule: List[TimeSlot], tasks: List[Task]) -> float:
        """Calculate fitness score for a schedule"""
        score = 0.0
        
        # Priority score - higher priority tasks scheduled earlier
        for i, slot in enumerate(schedule):
            if slot.task and not slot.is_break:
                # Earlier slots get higher weight
                time_weight = 1.0 - (i / len(schedule))
                score += slot.task.priority * time_weight * 10
        
        # Deadline compliance
        for slot in schedule:
            if slot.task and slot.task.deadline:
                if slot.end_time <= slot.task.deadline:
                    score += 20  # Bonus for meeting deadline
                else:
                    # Penalty proportional to how late
                    hours_late = (slot.end_time - slot.task.deadline).total_seconds() / 3600
                    score -= hours_late * 10
        
        # Preferred time compliance
        for slot in schedule:
            if slot.task and slot.task.preferred_time:
                hour = slot.start_time.hour
                if slot.task.preferred_time == 'morning' and 6 <= hour < 12:
                    score += 5
                elif slot.task.preferred_time == 'afternoon' and 12 <= hour < 17:
                    score += 5
                elif slot.task.preferred_time == 'evening' and 17 <= hour < 22:
                    score += 5
        
        # Penalize unscheduled tasks
        scheduled_task_ids = {slot.task.id for slot in schedule if slot.task}
        unscheduled_count = len([t for t in tasks if t.id not in scheduled_task_ids])
        score -= unscheduled_count * 50
        
        # Bonus for balanced break distribution
        break_intervals = []
        last_break_time = schedule[0].start_time if schedule else None
        
        for slot in schedule:
            if slot.is_break and last_break_time:
                interval = (slot.start_time - last_break_time).total_seconds() / 3600
                break_intervals.append(interval)
                last_break_time = slot.end_time
        
        if break_intervals:
            # Lower variance in break intervals is better
            variance = np.var(break_intervals)
            score += 10 / (1 + variance)
        
        return score
    
    def crossover(self, parent1: List[TimeSlot], parent2: List[TimeSlot]) -> List[TimeSlot]:
        """Create offspring by combining two parent schedules"""
        # Extract tasks from both parents
        tasks1 = [slot.task for slot in parent1 if slot.task and not slot.is_break]
        tasks2 = [slot.task for slot in parent2 if slot.task and not slot.is_break]
        
        # Combine unique tasks
        all_tasks = []
        seen_ids = set()
        
        # Take first half from parent1, second half from parent2
        split_point = len(tasks1) // 2
        
        for task in tasks1[:split_point] + tasks2[split_point:]:
            if task and task.id not in seen_ids:
                all_tasks.append(task)
                seen_ids.add(task.id)
        
        # Add any missing tasks
        for task in tasks1 + tasks2:
            if task and task.id not in seen_ids:
                all_tasks.append(task)
                seen_ids.add(task.id)
        
        # Create new schedule with combined tasks
        date = parent1[0].start_time.date() if parent1 else datetime.now().date()
        return self._create_random_schedule(all_tasks, datetime.combine(date, datetime.min.time()))
    
    def mutate(self, schedule: List[TimeSlot]) -> List[TimeSlot]:
        """Apply random mutation to a schedule"""
        if random.random() > self.mutation_rate:
            return schedule
        
        mutated = copy.deepcopy(schedule)
        
        # Swap two random tasks
        task_slots = [i for i, slot in enumerate(mutated) if slot.task and not slot.is_break]
        
        if len(task_slots) >= 2:
            idx1, idx2 = random.sample(task_slots, 2)
            mutated[idx1].task, mutated[idx2].task = mutated[idx2].task, mutated[idx1].task
        
        return mutated
    
    def optimize_schedule(self, tasks: List[Task], date: datetime) -> List[TimeSlot]:
        """Main optimization function using genetic algorithm"""
        # Generate initial population
        population = self.create_initial_population(tasks, date)
        
        for generation in range(self.generations):
            # Calculate fitness for each schedule
            fitness_scores = [(schedule, self.fitness(schedule, tasks)) 
                            for schedule in population]
            
            # Sort by fitness (descending)
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Select elite schedules
            elite = [schedule for schedule, _ in fitness_scores[:self.elite_size]]
            
            # Create new generation
            new_population = elite.copy()
            
            while len(new_population) < self.population_size:
                # Tournament selection
                parent1 = self._tournament_selection(fitness_scores)
                parent2 = self._tournament_selection(fitness_scores)
                
                # Crossover
                offspring = self.crossover(parent1, parent2)
                
                # Mutation
                offspring = self.mutate(offspring)
                
                new_population.append(offspring)
            
            population = new_population
        
        # Return best schedule
        final_scores = [(schedule, self.fitness(schedule, tasks)) 
                       for schedule in population]
        final_scores.sort(key=lambda x: x[1], reverse=True)
        
        return final_scores[0][0]
    
    def _tournament_selection(self, fitness_scores: List[Tuple[List[TimeSlot], float]], 
                            tournament_size: int = 5) -> List[TimeSlot]:
        """Select a parent using tournament selection"""
        tournament = random.sample(fitness_scores, tournament_size)
        tournament.sort(key=lambda x: x[1], reverse=True)
        return tournament[0][0]
    
    def reschedule_unfinished_tasks(self, current_schedule: List[TimeSlot], 
                                   new_tasks: List[Task], date: datetime) -> List[TimeSlot]:
        """Reschedule unfinished tasks from current schedule along with new tasks"""
        # Extract unfinished tasks
        unfinished_tasks = []
        for slot in current_schedule:
            if slot.task and not slot.task.completed:
                # Adjust priority for unfinished tasks
                task_copy = copy.deepcopy(slot.task)
                task_copy.priority = min(5, task_copy.priority + 1)  # Increase priority
                unfinished_tasks.append(task_copy)
        
        # Combine with new tasks
        all_tasks = unfinished_tasks + new_tasks
        
        # Optimize new schedule
        return self.optimize_schedule(all_tasks, date) 