from datetime import datetime
from Models.tests import TestCase, TestStep
from Service.browserAgent import BrowserAgent
from Service.testReporter import TestReporter
from Service.testStepsGenerator import PlaywrightCodeGenerator
from Service.userStoryExtractor import UserStoryExtractor


class AITestAutomation:
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.extractor = UserStoryExtractor(excel_path)
        self.code_generator = PlaywrightCodeGenerator()
        self.browser_agent = BrowserAgent()
        self.reporter = TestReporter()
        self.test_cases = []
        
    async def run(self):
        """Run the entire automation process."""
        print("Starting AI Test Automation")
        
        # 1. Extract user stories
        print("Extracting user stories from Excel...")
        user_stories = self.extractor.extract_user_stories()
        print(f"Found {len(user_stories)} user stories")
        
        # Start the browser
        await self.browser_agent.start()
        
        # 2. Process each user story
        for i, story in enumerate(user_stories):
            print(f"\nProcessing user story {i+1}/{len(user_stories)}")
            print(f"User Story: {story}")
            
            # Create a test case
            test_case = TestCase(
                id=f"TC_{i+1}",
                user_story=story,
                start_time=datetime.now().isoformat()
            )
            
            try:
                # Generate test steps
                print("Generating test steps...")
                steps_data = await self.code_generator.generate_test_steps(story)
                
                # Convert to TestStep objects
                test_steps = []
                for step_data in steps_data:
                    test_step = TestStep(
                        step_number=step_data.get("step_number", 0),
                        action=step_data.get("action", ""),
                        element_selector=step_data.get("element_selector"),
                        input_value=step_data.get("input_value"),
                        expected_result=step_data.get("expected_result")
                    )
                    test_steps.append(test_step)
                
                test_case.steps = test_steps
                
                # Execute the steps
                print("Executing test steps...")
                all_passed = True
                for i, step in enumerate(test_case.steps):
                    print(f"Step {i+1}: {step.action}")
                    
                    # Execute the step
                    updated_step = await self.browser_agent.execute_step(step)
                    test_case.steps[i] = updated_step
                    
                    # Update status
                    if updated_step.status != "Pass":
                        all_passed = False
                        print(f"  Status: {updated_step.status} - {updated_step.notes}")
                    else:
                        print(f"  Status: {updated_step.status}")
                    
                    # After each step, analyze the page
                    if updated_step.status == "Pass":
                        analysis = await self.browser_agent.analyze_page_content()
                        print(f"Page Analysis: {analysis['summary'][:100]}...")
                
                # Analyze the final state
                final_analysis = await self.browser_agent.analyze_page_content()
                test_case.summary = final_analysis["summary"]
                
                # Set the test case status
                test_case.status = "Pass" if all_passed else "Fail"
                
            except Exception as e:
                print(f"Error processing user story: {e}")
                test_case.status = "Error"
                test_case.summary = f"An error occurred: {str(e)}"
            
            # Record end time
            test_case.end_time = datetime.now().isoformat()
            test_case.duration_seconds = (
                datetime.fromisoformat(test_case.end_time) - 
                datetime.fromisoformat(test_case.start_time)
            ).total_seconds()
            
            # Generate report
            print("Generating test report...")
            report_path = self.reporter.generate_report(test_case)
            test_case.html_report_path = report_path
            
            # Save the test case
            self.test_cases.append(test_case)
            
            print(f"Test case {test_case.id} completed with status: {test_case.status}")
            print(f"Report generated at: {report_path}")
        
        # Clean up
        await self.browser_agent.stop()
        
        # Print final summary
        print("\n=== Test Automation Summary ===")
        print(f"Total test cases: {len(self.test_cases)}")
        passed = sum(1 for tc in self.test_cases if tc.status == "Pass")
        failed = sum(1 for tc in self.test_cases if tc.status == "Fail")
        errors = sum(1 for tc in self.test_cases if tc.status == "Error")
        print(f"Passed: {passed}, Failed: {failed}, Errors: {errors}")
        
        return self.test_cases
