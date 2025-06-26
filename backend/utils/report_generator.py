from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io
import os
from typing import List, Dict

class ReportGenerator:
    """Generate PDF reports for schedule analytics"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        custom_styles = {}
        
        # Title style
        custom_styles['CustomTitle'] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6366f1'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        # Subtitle style
        custom_styles['CustomSubtitle'] = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4f46e5'),
            spaceAfter=20
        )
        
        # Section header style
        custom_styles['SectionHeader'] = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#6366f1'),
            spaceAfter=12
        )
        
        return custom_styles
    
    def generate_weekly_report(self, stats_data: List[Dict], start_date: str, end_date: str) -> str:
        """Generate a weekly performance report"""
        filename = f"weekly_report_{start_date}_{end_date}.pdf"
        filepath = os.path.join('reports', filename)
        
        # Ensure reports directory exists
        os.makedirs('reports', exist_ok=True)
        
        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build story
        story = []
        
        # Add title
        title = Paragraph(
            f"Weekly Performance Report",
            self.custom_styles['CustomTitle']
        )
        story.append(title)
        
        # Add date range
        date_range = Paragraph(
            f"{self._format_date(start_date)} - {self._format_date(end_date)}",
            self.styles['Normal']
        )
        story.append(date_range)
        story.append(Spacer(1, 0.5*inch))
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(stats_data)
        
        # Add summary section
        story.append(Paragraph("Executive Summary", self.custom_styles['CustomSubtitle']))
        summary_table = self._create_summary_table(summary_stats)
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Add completion chart
        story.append(Paragraph("Daily Completion Rates", self.custom_styles['SectionHeader']))
        completion_chart = self._create_completion_chart(stats_data)
        if completion_chart:
            story.append(completion_chart)
            story.append(Spacer(1, 0.5*inch))
        
        # Add task breakdown
        story.append(Paragraph("Task Analysis", self.custom_styles['SectionHeader']))
        task_table = self._create_task_breakdown_table(stats_data)
        story.append(task_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Add productivity insights
        story.append(Paragraph("Productivity Insights", self.custom_styles['SectionHeader']))
        insights = self._generate_insights(summary_stats, stats_data)
        for insight in insights:
            story.append(Paragraph(f"• {insight}", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def _calculate_summary_stats(self, stats_data: List[Dict]) -> Dict:
        """Calculate summary statistics from raw data"""
        if not stats_data:
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'completion_rate': 0,
                'total_hours': 0,
                'avg_daily_tasks': 0,
                'most_productive_day': 'N/A',
                'least_productive_day': 'N/A'
            }
        
        total_tasks = sum(1 for stat in stats_data if not stat.get('is_break', False))
        completed_tasks = sum(1 for stat in stats_data if stat.get('completed', False))
        total_minutes = sum(stat.get('duration', 0) for stat in stats_data if stat.get('completed', False))
        
        # Group by date
        daily_stats = {}
        for stat in stats_data:
            date = stat['date']
            if date not in daily_stats:
                daily_stats[date] = {'total': 0, 'completed': 0, 'minutes': 0}
            
            if not stat.get('is_break', False):
                daily_stats[date]['total'] += 1
                if stat.get('completed', False):
                    daily_stats[date]['completed'] += 1
                    daily_stats[date]['minutes'] += stat.get('duration', 0)
        
        # Find most/least productive days
        most_productive = max(daily_stats.items(), key=lambda x: x[1]['minutes'], default=(None, {}))
        least_productive = min(daily_stats.items(), key=lambda x: x[1]['minutes'], default=(None, {}))
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'total_hours': round(total_minutes / 60, 1),
            'avg_daily_tasks': round(total_tasks / len(daily_stats), 1) if daily_stats else 0,
            'most_productive_day': most_productive[0] if most_productive[0] else 'N/A',
            'least_productive_day': least_productive[0] if least_productive[0] else 'N/A'
        }
    
    def _create_summary_table(self, summary_stats: Dict) -> Table:
        """Create summary statistics table"""
        data = [
            ['Metric', 'Value'],
            ['Total Tasks', str(summary_stats['total_tasks'])],
            ['Completed Tasks', str(summary_stats['completed_tasks'])],
            ['Completion Rate', f"{summary_stats['completion_rate']:.1f}%"],
            ['Total Productive Hours', f"{summary_stats['total_hours']} hrs"],
            ['Average Daily Tasks', str(summary_stats['avg_daily_tasks'])],
            ['Most Productive Day', self._format_date(summary_stats['most_productive_day'])],
            ['Least Productive Day', self._format_date(summary_stats['least_productive_day'])]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return table
    
    def _create_completion_chart(self, stats_data: List[Dict]) -> ReportLabImage:
        """Create daily completion rate chart"""
        if not stats_data:
            return None
        
        # Group by date
        daily_completion = {}
        for stat in stats_data:
            date = stat['date']
            if date not in daily_completion:
                daily_completion[date] = {'total': 0, 'completed': 0}
            
            if not stat.get('is_break', False):
                daily_completion[date]['total'] += 1
                if stat.get('completed', False):
                    daily_completion[date]['completed'] += 1
        
        # Sort by date
        sorted_dates = sorted(daily_completion.keys())
        
        # Calculate completion rates
        dates = []
        rates = []
        for date in sorted_dates:
            dates.append(self._format_date_short(date))
            total = daily_completion[date]['total']
            completed = daily_completion[date]['completed']
            rate = (completed / total * 100) if total > 0 else 0
            rates.append(rate)
        
        # Create chart
        plt.figure(figsize=(8, 4))
        plt.bar(dates, rates, color='#6366f1', alpha=0.8)
        plt.axhline(y=80, color='#10b981', linestyle='--', label='Target (80%)')
        plt.xlabel('Date')
        plt.ylabel('Completion Rate (%)')
        plt.title('Daily Task Completion Rates')
        plt.ylim(0, 110)
        plt.legend()
        plt.tight_layout()
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150)
        buffer.seek(0)
        plt.close()
        
        # Convert to ReportLab image
        img = ReportLabImage(buffer, width=6*inch, height=3*inch)
        return img
    
    def _create_task_breakdown_table(self, stats_data: List[Dict]) -> Table:
        """Create task breakdown by priority"""
        priority_stats = {i: {'total': 0, 'completed': 0} for i in range(1, 6)}
        
        for stat in stats_data:
            if not stat.get('is_break', False):
                priority = stat.get('priority', 3)
                priority_stats[priority]['total'] += 1
                if stat.get('completed', False):
                    priority_stats[priority]['completed'] += 1
        
        # Create table data
        data = [
            ['Priority', 'Total Tasks', 'Completed', 'Completion Rate']
        ]
        
        priority_names = {
            5: 'Critical',
            4: 'High',
            3: 'Medium',
            2: 'Low',
            1: 'Very Low'
        }
        
        for priority in range(5, 0, -1):
            stats = priority_stats[priority]
            if stats['total'] > 0:
                completion_rate = (stats['completed'] / stats['total'] * 100)
                data.append([
                    priority_names[priority],
                    str(stats['total']),
                    str(stats['completed']),
                    f"{completion_rate:.1f}%"
                ])
        
        table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        
        return table
    
    def _generate_insights(self, summary_stats: Dict, stats_data: List[Dict]) -> List[str]:
        """Generate productivity insights"""
        insights = []
        
        # Completion rate insight
        completion_rate = summary_stats['completion_rate']
        if completion_rate >= 80:
            insights.append(f"Excellent completion rate of {completion_rate:.1f}% - well above the 80% target!")
        elif completion_rate >= 60:
            insights.append(f"Good completion rate of {completion_rate:.1f}% - room for improvement to reach 80% target")
        else:
            insights.append(f"Completion rate of {completion_rate:.1f}% needs improvement - consider reducing task load")
        
        # Productivity trend
        if summary_stats['total_hours'] > 0:
            avg_hours_per_day = summary_stats['total_hours'] / 7
            if avg_hours_per_day >= 6:
                insights.append(f"High productivity with {avg_hours_per_day:.1f} productive hours per day")
            elif avg_hours_per_day >= 4:
                insights.append(f"Moderate productivity with {avg_hours_per_day:.1f} productive hours per day")
            else:
                insights.append(f"Low productivity with only {avg_hours_per_day:.1f} productive hours per day")
        
        # Task distribution insight
        high_priority_tasks = sum(1 for stat in stats_data if stat.get('priority', 3) >= 4)
        if high_priority_tasks > 0:
            high_priority_completed = sum(1 for stat in stats_data 
                                        if stat.get('priority', 3) >= 4 and stat.get('completed', False))
            high_priority_rate = (high_priority_completed / high_priority_tasks * 100)
            insights.append(f"High priority task completion rate: {high_priority_rate:.1f}%")
        
        # Most productive time insight
        time_slots = {}
        for stat in stats_data:
            if stat.get('completed', False) and 'schedule_data' in stat:
                # This would analyze time slots if schedule data is available
                pass
        
        return insights
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        if date_str == 'N/A':
            return date_str
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            return date_str
    
    def _format_date_short(self, date_str: str) -> str:
        """Format date string for charts"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%m/%d')
        except:
            return date_str 