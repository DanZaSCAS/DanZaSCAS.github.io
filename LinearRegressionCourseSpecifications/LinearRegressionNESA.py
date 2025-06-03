import numpy as np
from sklearn.linear_model import LinearRegression

# Create the data
x = np.array([[2], [4], [6], [8], [10], [12], [14], [16]])
y = np.array([1, 3, 5, 7, 9, 11, 13, 15])

# Create and train the model
model = LinearRegression()
model.fit(x, y)

# Make predictions
print("Prediction for 4:", model.predict([[4]]))      # → Should print 3
print("Prediction for 4.5:", model.predict([[4.5]]))  # → Should print 3.5

