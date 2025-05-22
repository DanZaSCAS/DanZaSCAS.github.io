import numpy as np
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, jsonify
import io
import base64
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error, r2_score

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/linear_regression', methods=['POST'])
def linear_regression():
    data = request.json
    x_values = np.array(data['x']).reshape(-1, 1)
    y_values = np.array(data['y'])
    
    # Fit linear regression model
    model = LinearRegression()
    model.fit(x_values, y_values)
    
    # Make predictions
    y_pred = model.predict(x_values)
    
    # Calculate metrics
    mse = mean_squared_error(y_values, y_pred)
    r2 = r2_score(y_values, y_pred)
    
    # Generate plot
    plt.figure(figsize=(10, 6))
    plt.scatter(x_values, y_values, color='blue', label='Data points')
    plt.plot(x_values, y_pred, color='red', label='Linear regression')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Linear Regression')
    plt.legend()
    plt.grid(True)
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return jsonify({
        'slope': float(model.coef_[0]),
        'intercept': float(model.intercept_),
        'mse': mse,
        'r2': r2,
        'plot': plot_data,
        'predictions': y_pred.tolist()
    })

@app.route('/api/polynomial_regression', methods=['POST'])
def polynomial_regression():
    data = request.json
    x_values = np.array(data['x']).reshape(-1, 1)
    y_values = np.array(data['y'])
    degree = data.get('degree', 2)
    
    # Create polynomial features
    poly = PolynomialFeatures(degree=degree)
    x_poly = poly.fit_transform(x_values)
    
    # Fit polynomial regression model
    model = LinearRegression()
    model.fit(x_poly, y_values)
    
    # Make predictions
    y_pred = model.predict(x_poly)
    
    # Calculate metrics
    mse = mean_squared_error(y_values, y_pred)
    r2 = r2_score(y_values, y_pred)
    
    # Generate plot with smooth curve
    x_curve = np.linspace(min(x_values)[0], max(x_values)[0], 100).reshape(-1, 1)
    x_curve_poly = poly.transform(x_curve)
    y_curve = model.predict(x_curve_poly)
    
    plt.figure(figsize=(10, 6))
    plt.scatter(x_values, y_values, color='blue', label='Data points')
    plt.plot(x_curve, y_curve, color='green', label=f'Polynomial (degree={degree})')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Polynomial Regression')
    plt.legend()
    plt.grid(True)
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return jsonify({
        'coefficients': model.coef_.tolist(),
        'intercept': float(model.intercept_),
        'mse': mse,
        'r2': r2,
        'plot': plot_data,
        'predictions': y_pred.tolist()
    })

@app.route('/api/logistic_regression', methods=['POST'])
def logistic_regression():
    data = request.json
    x_values = np.array(data['x']).reshape(-1, 1)
    y_values = np.array(data['y'])
    
    # Fit logistic regression model
    model = LogisticRegression()
    model.fit(x_values, y_values)
    
    # Make predictions
    y_pred_proba = model.predict_proba(x_values)[:, 1]
    y_pred = model.predict(x_values)
    
    # Generate plot
    plt.figure(figsize=(10, 6))
    plt.scatter(x_values, y_values, color='blue', label='Data points')
    
    # Create smooth curve for visualization
    x_curve = np.linspace(min(x_values)[0], max(x_values)[0], 100).reshape(-1, 1)
    y_curve = model.predict_proba(x_curve)[:, 1]
    
    plt.plot(x_curve, y_curve, color='purple', label='Logistic regression')
    plt.xlabel('X')
    plt.ylabel('Probability')
    plt.title('Logistic Regression')
    plt.legend()
    plt.grid(True)
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return jsonify({
        'coefficients': model.coef_[0].tolist(),
        'intercept': float(model.intercept_[0]),
        'plot': plot_data,
        'predictions': y_pred.tolist(),
        'probabilities': y_pred_proba.tolist()
    })

@app.route('/api/compare_regressions', methods=['POST'])
def compare_regressions():
    data = request.json
    x_values = np.array(data['x']).reshape(-1, 1)
    y_values = np.array(data['y'])
    poly_degree = data.get('degree', 2)
    
    # Linear regression
    linear_model = LinearRegression()
    linear_model.fit(x_values, y_values)
    linear_pred = linear_model.predict(x_values)
    
    # Polynomial regression
    poly = PolynomialFeatures(degree=poly_degree)
    x_poly = poly.fit_transform(x_values)
    poly_model = LinearRegression()
    poly_model.fit(x_poly, y_values)
    poly_pred = poly_model.predict(x_poly)
    
    # Generate comparison plot
    plt.figure(figsize=(12, 8))
    plt.scatter(x_values, y_values, color='blue', label='Data points')
    
    # Sort for smooth curves
    x_sorted = np.sort(x_values, axis=0)
    x_curve = np.linspace(min(x_values)[0], max(x_values)[0], 100).reshape(-1, 1)
    
    # Linear prediction line
    y_linear = linear_model.predict(x_curve)
    plt.plot(x_curve, y_linear, color='red', label='Linear regression')
    
    # Polynomial prediction curve
    x_curve_poly = poly.transform(x_curve)
    y_poly = poly_model.predict(x_curve_poly)
    plt.plot(x_curve, y_poly, color='green', label=f'Polynomial (degree={poly_degree})')
    
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Regression Comparison')
    plt.legend()
    plt.grid(True)
    
    # Convert plot to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    # Calculate metrics
    linear_mse = mean_squared_error(y_values, linear_pred)
    linear_r2 = r2_score(y_values, linear_pred)
    poly_mse = mean_squared_error(y_values, poly_pred)
    poly_r2 = r2_score(y_values, poly_pred)
    
    return jsonify({
        'plot': plot_data,
        'linear': {
            'slope': float(linear_model.coef_[0]),
            'intercept': float(linear_model.intercept_),
            'mse': linear_mse,
            'r2': linear_r2
        },
        'polynomial': {
            'coefficients': poly_model.coef_.tolist(),
            'intercept': float(poly_model.intercept_),
            'mse': poly_mse,
            'r2': poly_r2
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
