#!/usr/bin/env python
"""
Test new autonomous payment logic
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from django.conf import settings

def check_student_balances():
    """Check current student balances"""
    print("=== CHECKING STUDENT BALANCES ===")
    
    teocoin_service = TeoCoinService()
    student_address = '0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4'
    
    # Check TEO balance
    teo_balance = teocoin_service.get_balance(student_address)
    print(f"Student TEO balance: {teo_balance}")
    
    # Check MATIC balance (same way as in prerequisites)
    from web3 import Web3
    student_matic_wei = teocoin_service.w3.eth.get_balance(Web3.to_checksum_address(student_address))
    matic_balance = float(teocoin_service.w3.from_wei(student_matic_wei, 'ether'))
    print(f"Student MATIC balance: {matic_balance}")
    
    # Check prerequisites for a 15 TEO course
    from decimal import Decimal
    course_price = Decimal('15')
    prerequisites = teocoin_service.check_course_payment_prerequisites(
        student_address, course_price
    )
    
    print(f"\n=== PREREQUISITES FOR 15 TEO COURSE ===")
    print(f"Student has enough TEO: {prerequisites['student']['has_enough_teo']}")
    print(f"Student has enough MATIC: {prerequisites['student']['has_enough_matic']}")
    print(f"Reward pool has enough MATIC: {prerequisites['reward_pool']['has_enough_matic']}")
    print(f"Ready for payment: {prerequisites['ready']}")
    
    print(f"\nRequired TEO: {course_price}")
    print(f"Student TEO: {prerequisites['student']['teo_balance']}")
    print(f"Required MATIC: {prerequisites['student']['min_matic_required']}")
    print(f"Student MATIC: {prerequisites['student']['matic_balance']}")

if __name__ == '__main__':
    check_student_balances()
