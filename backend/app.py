from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup remains the same as your original code
Base = declarative_base()
engine = create_engine('sqlite:///budget.db', echo=True)
Session = sessionmaker(bind=engine)

# Models remain the same as your original code
# ... (keep all your existing model definitions)

# Modified API Routes
@app.route('/api/users', methods=['GET', 'POST'])
def users():
    session = Session()
    try:
        if request.method == 'GET':
            users = session.query(Employee).filter_by(is_active=True).all()
            return jsonify([{
                'id': user.id,
                'ldap': user.ldap,
                'firstName': user.first_name,
                'lastName': user.last_name,
                'email': user.email,
                'level': user.level
            } for user in users])
        else:
            data = request.json
            employee = Employee(
                ldap=data['ldap'],
                first_name=data['firstName'],
                last_name=data['lastName'],
                email=data['email'],
                level=data['level']
            )
            session.add(employee)
            session.commit()
            return jsonify({'message': 'User created successfully', 'id': employee.id})
    finally:
        session.close()

@app.route('/api/aops', methods=['GET', 'POST'])
def aops():
    session = Session()
    try:
        if request.method == 'GET':
            aops = session.query(AOP).filter_by(is_active=True).all()
            return jsonify([{
                'id': aop.id,
                'name': aop.name,
                'totalAmount': aop.total_amount,
                'state': aop.state
            } for aop in aops])
        else:
            data = request.json
            aop = AOP(
                name=data['name'],
                total_amount=data['amount'],
                state=AOPState.DRAFT
            )
            session.add(aop)
            session.commit()
            return jsonify({'message': 'AOP created successfully', 'id': aop.id})
    finally:
        session.close()

@app.route('/api/budgets', methods=['GET', 'POST'])
def budgets():
    session = Session()
    try:
        if request.method == 'GET':
            aop_id = request.args.get('aopId')
            query = session.query(Budget).filter_by(is_active=True)
            if aop_id:
                query = query.filter_by(aop_id=aop_id)
            budgets = query.all()
            return jsonify([{
                'id': budget.id,
                'budgetId': budget.budget_id,
                'aopId': budget.aop_id,
                'project': budget.project,
                'amount': budget.amount
            } for budget in budgets])
        else:
            data = request.json
            budget = Budget(
                budget_id=f"BUD{datetime.now().strftime('%Y%m%d%H%M%S')}",
                aop_id=data['aopId'],
                project=data['project'],
                amount=data['amount']
            )
            session.add(budget)
            
            # Update AOP total amount
            aop = session.query(AOP).filter_by(id=data['aopId']).first()
            if aop:
                aop.total_amount += data['amount']
            
            session.commit()
            return jsonify({'message': 'Budget created successfully', 'id': budget.id})
    finally:
        session.close()

@app.route('/api/organization/<ldap>', methods=['GET'])
def organization(ldap):
    session = Session()
    try:
        employee = session.query(Employee).filter_by(ldap=ldap, is_active=True).first()
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        def get_reports(emp):
            return {
                'id': emp.id,
                'name': f"{emp.first_name} {emp.last_name}",
                'ldap': emp.ldap,
                'level': emp.level,
                'reports': [get_reports(report) for report in emp.reports if report.is_active]
            }
            
        return jsonify(get_reports(employee))
    finally:
        session.close()

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True)
