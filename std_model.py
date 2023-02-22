import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# Read in the data
df = pd.read_csv("hourly_data.csv")

# Separate the mean and standard deviation values
means = df.drop(['std', 'day_of_week', 'time_of_day'], axis=1)
stds = df.drop(['power', 'day_of_week', 'time_of_day'], axis=1)

# Train the linear regression model
model = LinearRegression()
model.fit(means, df['power'])

# Create an empty array to store the predictions
predictions = np.zeros((7, 24, 2))

# Loop through the days and hours and make predictions
for day in range(1, 8):  # Monday to Sunday
    for hour in range(0, 24):  # 0 to 23
        # Create a new row of data with the day and hour values
        new_data = pd.DataFrame({
            'day_of_week': [day],
            'time_of_day': [f"{hour:02d}"]
        })

        # Look up the standard deviation for this day and hour
        std = stds[(stds['day_of_week'] == day) & (stds['time_of_day'] == f"{hour:02d}")]['std'].iloc[0]
        
        # Look up the standard deviation for the previous hour on this day
        if hour == 0:
            prev_std = stds[(stds['day_of_week'] == day - 1) & (stds['time_of_day'] == "23")]['std'].iloc[0]
        else:
            prev_std = stds[(stds['day_of_week'] == day) & (stds['time_of_day'] == f"{hour-1:02d}")]['std'].iloc[0]
        
        # Create a new row of data with the mean and standard deviation values
        new_data['power_mean'] = means['power'].mean()
        new_data['power_std'] = prev_std
        
        # Make a prediction with the linear regression model
        x = np.array(new_data.drop(['day_of_week', 'time_of_day'])).reshape(1, -1)
        y_pred = model.predict(x)[0]

        # Store the prediction and standard deviation in the array
        predictions[day-1, hour, 0] = y_pred
        predictions[day-1, hour, 1] = std

# Print the predictions array
print(predictions)
