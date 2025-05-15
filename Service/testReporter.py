from datetime import datetime
from pathlib import Path
import jinja2
from Models.tests import TestCase


class TestReporter:
    def __init__(self):
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath="./"),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Create a simple HTML template if it doesn't exist
        self.template_path = Path("test_report_template.html")
        if not self.template_path.exists():
            self._create_default_template()
            
    def _create_default_template(self):
        """Create a default HTML report template."""
        template_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Automation Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }
                h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { color: #2980b9; margin-top: 30px; }
                .summary { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .test-info { display: flex; flex-wrap: wrap; }
                .test-info div { margin-right: 30px; margin-bottom: 10px; }
                .steps { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .steps th, .steps td { border: 1px solid #ddd; padding: 10px; text-align: left; }
                .steps th { background-color: #f2f2f2; }
                .step-pass { background-color: #d4edda; }
                .step-fail { background-color: #f8d7da; }
                .screenshot { max-width: 800px; margin: 10px 0; border: 1px solid #ddd; }
                .notes { font-style: italic; color: #666; }
                .status-pass { color: #28a745; font-weight: bold; }
                .status-fail { color: #dc3545; font-weight: bold; }
                .status-not-run { color: #6c757d; font-weight: bold; }
                .page-analysis { background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>AI Automation Test Report</h1>
            
            <div class="summary">
                <h2>Test Summary</h2>
                <div class="test-info">
                    <div><strong>User Story:</strong> {{ test_case.user_story }}</div>
                    <div><strong>Status:</strong> <span class="status-{{ test_case.status|lower }}">{{ test_case.status }}</span></div>
                    <div><strong>Start Time:</strong> {{ test_case.start_time }}</div>
                    <div><strong>End Time:</strong> {{ test_case.end_time }}</div>
                    <div><strong>Duration:</strong> {{ test_case.duration_seconds }} seconds</div>
                </div>
            </div>
            
            {% if test_case.summary %}
            <div class="page-analysis">
                <h2>Test Summary</h2>
                <p>{{ test_case.summary }}</p>
            </div>
            {% endif %}
            
            <h2>Test Steps</h2>
            <table class="steps">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Action</th>
                        <th>Details</th>
                        <th>Expected Result</th>
                        <th>Status</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for step in test_case.steps %}
                    <tr class="step-{{ step.status|lower }}">
                        <td>{{ step.step_number }}</td>
                        <td>{{ step.action }}</td>
                        <td>
                            {% if step.element_selector %}Selector: {{ step.element_selector }}{% endif %}
                            {% if step.input_value %}<br>Value: {{ step.input_value }}{% endif %}
                        </td>
                        <td>{{ step.expected_result }}</td>
                        <td class="status-{{ step.status|lower }}">{{ step.status }}</td>
                        <td>{{ step.notes }}</td>
                    </tr>
                    {% if step.screenshot_path %}
                    <tr class="step-{{ step.status|lower }}">
                        <td colspan="6">
                            <img src="{{ step.screenshot_path }}" alt="Step {{ step.step_number }} Screenshot" class="screenshot">
                        </td>
                    </tr>
                    {% endif %}
                    {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
        """
        with open(self.template_path, "w") as f:
            f.write(template_content)
    
    def generate_report(self, test_case: TestCase) -> str:
        """Generate HTML report for a test case."""
        try:
            template = self.template_env.get_template(self.template_path.name)
            html_content = template.render(test_case=test_case)
            
            # Write to file
            report_dir = Path("./utils/test_results/reports")
            report_dir.mkdir(exist_ok=True, parents=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"report_{test_case.id}_{timestamp}.html"
            
            with open(report_path, "w") as f:
                f.write(html_content)
                
            return str(report_path)
        except Exception as e:
            print(f"Error generating report: {e}")
            return ""