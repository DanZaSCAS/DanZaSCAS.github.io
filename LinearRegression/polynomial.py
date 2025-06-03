"""
HSC Software Engineering - Simple Polynomial Regression
======================================================

Beginner-friendly polynomial regression using OOP.
Polynomial regression finds CURVED lines through data (not straight lines).

Real example: Uber pricing changes throughout the day in a curve pattern.

pip install numpy scikit-learn matplotlib



"""

import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression


class SimplePolynomialRegression:
    """
    Simple polynomial regression class for HSC students.
    
    What it does: Finds curved lines through data points.
    Why: Some real-world data follows curves, not straight lines.
    """
    
    def __init__(self):
        """Set up the model - ready to learn from data."""
        self.poly_features = PolynomialFeatures(degree=2)  # degree=2 means curved line
        self.model = LinearRegression()
        self.is_trained = False
        print("Polynomial regression model created - ready for training!")
    
    def train(self, x_data, y_data):
        """
        Train the model with labeled data (supervised learning).
        
        x_data: input values (like hours of day)
        y_data: correct answers (like Uber prices)
        """
        # Convert regular numbers to polynomial features
        # Example: [1, 2, 3] becomes [[1, 1, 1], [2, 4, 8], [3, 9, 27]]
        x_poly = self.poly_features.fit_transform(np.array(x_data).reshape(-1, 1))
        
        # Learn the pattern from the training data
        self.model.fit(x_poly, y_data)
        self.is_trained = True
        print(f"Training complete! Learned from {len(x_data)} examples.")
    
    def predict(self, new_x):
        """
        Make predictions for new input values.
        
        new_x: new input to predict (like a new hour of day)
        Returns: predicted value (like predicted Uber price)
        """
        if not self.is_trained:
            print("Error: Must train the model first!")
            return None
        
        # Convert new input to polynomial features
        new_x_poly = self.poly_features.transform(np.array(new_x).reshape(-1, 1))
        
        # Make prediction
        prediction = self.model.predict(new_x_poly)
        return prediction[0]


# Simple example for students
def uber_pricing_example():
    """Real-world example: Uber surge pricing throughout the day."""
    
    print("=== UBER SURGE PRICING EXAMPLE ===")
    print("Problem: Predict Uber surge pricing at different times")
    print("Pattern: Prices are high during rush hours, low during midday\n")
    
    # Training data (this is our labeled data for supervised learning)
    hours = [8, 12, 16, 20]           # Hours of day
    surge_prices = [2.5, 1.0, 1.5, 3.0]  # Surge multipliers
    
    print("Training Data:")
    for hour, price in zip(hours, surge_prices):
        print(f"  {hour}:00 → {price}x surge multiplier")
    
    # Create and train the model
    model = SimplePolynomialRegression()
    model.train(hours, surge_prices)
    
    # Make predictions for new times
    print("\nMaking Predictions:")
    test_hours = [10, 14, 18]
    
    for hour in test_hours:
        predicted_surge = model.predict([hour])
        print(f"  {hour}:00 → Predicted surge: {predicted_surge:.2f}x")
    
    print("\nWhy polynomial regression?")
    print("- Uber pricing follows a CURVE (high-low-high pattern)")
    print("- Linear regression only draws STRAIGHT lines")
    print("- Polynomial regression can draw CURVED lines!")


# Student exercise
def student_grades_example():
    """Example: Student grades improving over time (curved growth)."""
    
    print("\n=== STUDENT GRADES EXAMPLE ===")
    print("Problem: Predict how grades improve during semester")
    print("Pattern: Fast improvement at start, then levels off\n")
    
    # Training data
    weeks = [2, 6, 10, 14]        # Weeks into semester  
    grades = [50, 70, 80, 85]     # Grade percentages
    
    print("Training Data:")
    for week, grade in zip(weeks, grades):
        print(f"  Week {week} → {grade}% grade")
    
    # Train model
    model = SimplePolynomialRegression()
    model.train(weeks, grades)
    
    # Predict future grades
    print("\nPredictions:")
    future_weeks = [4, 8, 12, 16]
    
    for week in future_weeks:
        predicted_grade = model.predict([week])
        print(f"  Week {week} → Predicted grade: {predicted_grade:.1f}%")


# Run examples
if __name__ == "__main__":
    uber_pricing_example()
    student_grades_example()
    
    print("\n=== KEY LEARNING POINTS ===")
    print("1. Polynomial regression finds CURVED patterns")
    print("2. Uses supervised learning (needs training data)")
    print("3. Better than linear regression for curved data")
    print("4. Real applications: pricing, growth, trends")