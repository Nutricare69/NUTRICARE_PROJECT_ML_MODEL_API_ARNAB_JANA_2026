# 🥗 NUTRI-CARE: AI-Powered Personalized Indian Diet Planner API
### Final Year Group Project | Machine Learning + FastAPI
## Contribution in this repository: Arnab Jana

<h1 align="center">🥗 NUTRI-CARE API</h1>

<h3 align="center">AI-Powered Indian Diet Planner</h3>

<p align="center">

<img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi"/>
<img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python"/>
<img src="https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=jsonwebtokens"/>
<img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge"/>

</p>

<hr>

<h2>📌 Overview</h2>

<p>
<b>NUTRI-CARE</b> is a <b>personalized AI-powered diet planning backend</b> that generates 
<b>7-day Indian meal plans</b> based on:
</p>

<ul>
<li>User fitness goals</li>
<li>Dietary preferences</li>
<li>Allergies</li>
<li>Medical conditions</li>
<li>Activity level</li>
</ul>

<p>
It uses a <b>smart scoring algorithm</b> and a rich dataset of Indian foods to recommend meals
that best match the user's nutritional needs.
</p>

<hr>

<h2>📚 Table of Contents</h2>

<ul>
<li>✨ Features</li>
<li>🛠 Tech Stack</li>
<li>📁 Project Structure</li>
<li>🔧 Installation</li>
<li>🚀 Running the API</li>
<li>📖 API Documentation</li>
<li>🔐 Authentication</li>
<li>📌 Key Endpoints</li>
<li>🔄 Sample Workflow</li>
<li>📸 Screenshots</li>
<li>🤝 Contributing</li>
<li>📄 License</li>
</ul>

<hr>

<h2>✨ Features</h2>

<h3>✅ User authentication using JWT</h3>

<ul>
<li>User registration</li>
<li>Login for users and admins</li>
</ul>

<hr>

<h3>✅ Personalized meal planning based on</h3>

<ul>
<li>Goal (Weight Loss / Muscle Gain / Maintenance)</li>
<li>Food preference (Vegetarian / Eggetarian / Non-Vegetarian)</li>
<li>Allergies (Gluten, Dairy, Nuts)</li>
<li>Medical conditions (Diabetes, Hypertension)</li>
<li>Activity level</li>
</ul>

<hr>

<h3>✅ Smart meal recommendation</h3>

<ul>
<li>Dynamic food scoring algorithm</li>
<li>Matches food macros with user goals</li>
<li>Selects optimal foods from dataset</li>
</ul>

<hr>

<h3>✅ 7-Day Meal Plan Generator</h3>

<ul>
<li>Randomly sampled from top-scored foods</li>
<li>Balanced nutritional recommendations</li>
</ul>

<hr>

<h3>✅ User Profile System</h3>

<ul>
<li>BMI calculation</li>
<li>TDEE calculation</li>
<li>Plan history tracking</li>
</ul>

<hr>

<h3>✅ Admin Dashboard</h3>

<ul>
<li>View users</li>
<li>Manage user accounts</li>
<li>System statistics</li>
</ul>

<hr>

<h3>✅ Mock Food Image Analysis</h3>

<ul>
<li>Placeholder for AI food recognition</li>
</ul>

<hr>

<h3>✅ Interactive API Documentation</h3>

<ul>
<li>Swagger UI</li>
<li>ReDoc</li>
</ul>

<hr>

<h2>🛠 Tech Stack</h2>

<table>
<tr>
<th>Component</th>
<th>Technology</th>
</tr>

<tr>
<td>Backend Framework</td>
<td>
<img src="https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi"/> FastAPI
</td>
</tr>

<tr>
<td>Data Processing</td>
<td>
<img src="https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas"/> Pandas
</td>
</tr>

<tr>
<td>Authentication</td>
<td>
<img src="https://img.shields.io/badge/JWT-black?style=flat&logo=jsonwebtokens"/> JWT
</td>
</tr>

<tr>
<td>Password Hashing</td>
<td>SHA-256 (hashlib)</td>
</tr>

<tr>
<td>Data Storage</td>
<td>JSON File</td>
</tr>

<tr>
<td>Language</td>
<td>Python 3.9+</td>
</tr>

</table>

<hr>

<h2>📁 Project Structure</h2>

<pre>
backend/
│
├── routers/
│   ├── admin.py
│   ├── analysis.py
│   ├── auth.py
│   ├── foods.py
│   ├── meal_plan.py
│   └── users.py
│
├── utils/
│   ├── data.py
│   └── storage.py
│
├── Cleaned_Indian_Food_Dataset.csv
├── dependencies.py
├── main.py
├── models.py
├── requirements.txt
└── users.json
</pre>

<hr>

<h2>🔧 Installation</h2>

<h3>1️⃣ Clone Repository</h3>

<pre>
git clone https://github.com/yourusername/nutri-care-api.git
cd nutri-care-api/backend
</pre>

<hr>

<h3>2️⃣ Create Virtual Environment</h3>

<pre>
python -m venv venv
</pre>

Activate it

<b>Windows</b>

<pre>
venv\Scripts\activate
</pre>

<b>Mac/Linux</b>

<pre>
source venv/bin/activate
</pre>

<hr>

<h3>3️⃣ Install Dependencies</h3>

<pre>
pip install -r requirements.txt
</pre>

<hr>

<h3>4️⃣ Ensure Dataset Exists</h3>

<p>
Make sure the file exists inside <b>backend/</b>
</p>

<pre>
Cleaned_Indian_Food_Dataset.csv
</pre>

<p>If missing, the system will automatically generate a synthetic dataset.</p>

<hr>

<h2>🚀 Running the API</h2>

<pre>
uvicorn main:app --reload
</pre>

Server will start at

<pre>
http://127.0.0.1:8000
</pre>

<hr>

<h2>📖 API Documentation</h2>

<p>FastAPI automatically provides interactive documentation.</p>

<b>Swagger UI</b>

<pre>
http://127.0.0.1:8000/docs
</pre>

<b>ReDoc</b>

<pre>
http://127.0.0.1:8000/redoc
</pre>

<hr>

<h2>🔐 Authentication</h2>

Most endpoints require a <b>JWT Bearer Token</b>.

<h3>Register</h3>

<pre>
POST /api/auth/register
</pre>

<pre>
{
 "username": "user1",
 "password": "password",
 "email": "user@email.com",
 "name": "User Name"
}
</pre>

<hr>

<h3>Login</h3>

<pre>
POST /api/auth/login
</pre>

<pre>
{
 "username": "user1",
 "password": "password"
}
</pre>

<hr>

<h3>Authorization Header</h3>

<pre>
Authorization: Bearer &lt;your_access_token&gt;
</pre>

<hr>

<h2>📌 Key Endpoints</h2>

<h3>👤 User</h3>

<table>
<tr>
<th>Method</th>
<th>Endpoint</th>
<th>Description</th>
</tr>

<tr>
<td>GET</td>
<td>/api/user/profile</td>
<td>Get latest profile</td>
</tr>

<tr>
<td>POST</td>
<td>/api/user/profile</td>
<td>Save profile (BMI + TDEE)</td>
</tr>

<tr>
<td>GET</td>
<td>/api/user/history</td>
<td>Retrieve history</td>
</tr>

</table>

<hr>

<h3>🍽 Meal Plan</h3>

<table>
<tr>
<th>Method</th>
<th>Endpoint</th>
<th>Description</th>
</tr>

<tr>
<td>POST</td>
<td>/api/meal-plan/generate</td>
<td>Generate 7-day meal plan</td>
</tr>

<tr>
<td>GET</td>
<td>/api/meal-plan/saved</td>
<td>View saved plans</td>
</tr>

</table>

<hr>

<h2>📸 Screenshots</h2>

<table>
<tr>
<th>Swagger UI</th>
<th>Meal Plan</th>
</tr>

<tr>
<td><img src="https://via.placeholder.com/400x300?text=Swagger+UI"></td>
<td><img src="https://via.placeholder.com/400x300?text=Meal+Plan+JSON"></td>
</tr>
</table>

<hr>

<h2>🤝 Contributing</h2>

<p>Contributions are welcome.</p>

<pre>
Fork repository
Create feature branch
Commit changes
Push branch
Open Pull Request
</pre>

Example:

<pre>
git checkout -b feature/amazing-feature
git commit -m "Added amazing feature"
git push origin feature/amazing-feature
</pre>

<hr>

<h2>📄 License</h2>

<p>This project is licensed under the <b>MIT License</b>.</p>

<hr>

<h2>🙌 Acknowledgements</h2>

<ul>
<li>Indian food dataset compiled from public sources</li>
<li>Inspired by culturally relevant diet planning</li>
<li>Built using FastAPI and Python</li>
</ul>
