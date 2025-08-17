#!/usr/bin/env python3
"""
Comprehensive Test Suite for TeoCoin Discount System

This script tests the complete discount system end-to-end:
1. Smart contract functionality
2. Backend service operations
3. API endpoints
4. Integration flows

Run after deploying the TeoCoinDiscount contract.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
import django
django.setup()

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from blockchain.blockchain import TeoCoinService
from services.teocoin_discount_service import teocoin_discount_service


class DiscountSystemTester:
    """Comprehensive test suite for the discount system"""
    
    def __init__(self):
        self.teocoin_service = TeoCoinService()
        self.w3 = self.teocoin_service.w3
        self.test_results = []
        
        # Test accounts (you'll need to create these)
        self.student_private_key = os.getenv('TEST_STUDENT_PRIVATE_KEY')
        self.teacher_private_key = os.getenv('TEST_TEACHER_PRIVATE_KEY')
        
        if self.student_private_key:
            self.student_account = Account.from_key(self.student_private_key)
            self.student_address = self.student_account.address
        else:
            self.student_account = None
            self.student_address = None
            
        if self.teacher_private_key:
            self.teacher_account = Account.from_key(self.teacher_private_key)
            self.teacher_address = self.teacher_account.address
        else:
            self.teacher_account = None
            self.teacher_address = None
    
    def log_test(self, test_name, success, message="", details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_contract_deployment(self):
        """Test 1: Verify contract is deployed and accessible"""
        print("\n📋 TEST 1: Contract Deployment Verification")
        print("-" * 50)
        
        try:
            # Check if discount service is initialized
            if not teocoin_discount_service.discount_contract:
                self.log_test("Contract Initialization", False, "Discount service not initialized")
                return False
            
            # Test basic contract calls
            contract = teocoin_discount_service.discount_contract
            
            # Test read functions
            teo_token = contract.functions.teoToken().call()
            reward_pool = contract.functions.rewardPool().call()
            platform_account = contract.functions.platformAccount().call()
            
            self.log_test("Contract Read Functions", True, f"TEO: {teo_token}, Pool: {reward_pool}")
            
            # Test cost calculation
            teo_cost, teacher_bonus = contract.functions.calculateTeoCost(10000, 10).call()  # €100, 10%
            expected_teo = 10000 * 10 // 100 * 10  # Discount value * TEO rate
            expected_bonus = expected_teo * 25 // 100
            
            if teo_cost == expected_teo and teacher_bonus == expected_bonus:
                self.log_test("Cost Calculation", True, f"10% on €100 = {teo_cost / 10**18:.2f} TEO + {teacher_bonus / 10**18:.2f} bonus")
            else:
                self.log_test("Cost Calculation", False, f"Expected {expected_teo}, got {teo_cost}")
            
            return True
            
        except Exception as e:
            self.log_test("Contract Deployment", False, f"Error: {e}")
            return False
    
    def test_backend_service(self):
        """Test 2: Backend service functionality"""
        print("\n🔧 TEST 2: Backend Service Testing")
        print("-" * 50)
        
        try:
            # Test cost calculation
            teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                Decimal('100'), 10
            )
            
            expected_cost = 100 * 10 * 10 * 10**18 // 100  # €100 * 10% * 10 TEO/EUR
            expected_bonus = expected_cost * 25 // 100
            
            if teo_cost == expected_cost and teacher_bonus == expected_bonus:
                self.log_test("Service Cost Calculation", True, f"Calculated {teo_cost / 10**18:.2f} TEO correctly")
            else:
                self.log_test("Service Cost Calculation", False, f"Expected {expected_cost}, got {teo_cost}")
            
            # Test signature generation (if we have test accounts)
            if self.student_address:
                signature_data = teocoin_discount_service.generate_student_signature_data(
                    self.student_address, 123, teo_cost
                )
                
                if 'message_hash' in signature_data and 'signable_message' in signature_data:
                    self.log_test("Signature Generation", True, "Signature data generated correctly")
                else:
                    self.log_test("Signature Generation", False, "Invalid signature data structure")
            else:
                self.log_test("Signature Generation", False, "No test student account configured")
            
            return True
            
        except Exception as e:
            self.log_test("Backend Service", False, f"Error: {e}")
            return False
    
    def test_account_balances(self):
        """Test 3: Check test account balances"""
        print("\n💰 TEST 3: Account Balance Verification")
        print("-" * 50)
        
        try:
            if self.student_address:
                # Check MATIC balance
                matic_balance = self.w3.eth.get_balance(self.student_address)
                matic_balance_formatted = self.w3.from_wei(matic_balance, 'ether')
                
                # Check TEO balance
                teo_balance = self.teocoin_service.get_balance(self.student_address)
                
                self.log_test("Student Account Balance", True, 
                            f"MATIC: {matic_balance_formatted:.4f}, TEO: {teo_balance}")
            else:
                self.log_test("Student Account Balance", False, "No student account configured")
            
            if self.teacher_address:
                # Check teacher balances
                matic_balance = self.w3.eth.get_balance(self.teacher_address)
                matic_balance_formatted = self.w3.from_wei(matic_balance, 'ether')
                teo_balance = self.teocoin_service.get_balance(self.teacher_address)
                
                self.log_test("Teacher Account Balance", True,
                            f"MATIC: {matic_balance_formatted:.4f}, TEO: {teo_balance}")
            else:
                self.log_test("Teacher Account Balance", False, "No teacher account configured")
            
            # Check reward pool balance
            reward_pool_balance = self.teocoin_service.get_reward_pool_balance()
            self.log_test("Reward Pool Balance", True, f"Pool: {reward_pool_balance} TEO")
            
            return True
            
        except Exception as e:
            self.log_test("Account Balances", False, f"Error: {e}")
            return False
    
    def test_signature_flow(self):
        """Test 4: Signature generation and verification"""
        print("\n✍️ TEST 4: Signature Flow Testing")
        print("-" * 50)
        
        if not self.student_account:
            self.log_test("Signature Flow", False, "No student account for testing")
            return False
        
        try:
            # Generate signature data
            course_id = 123
            teo_cost = 100 * 10**18  # 100 TEO
            
            signature_data = teocoin_discount_service.generate_student_signature_data(
                self.student_address, course_id, teo_cost
            )
            
            # Sign the message
            message = signature_data['signable_message']
            signature = self.student_account.sign_message(message)
            
            self.log_test("Message Signing", True, f"Signed message with signature: {signature.signature.hex()}")
            
            # Verify the signature matches what the contract expects
            message_hash = Web3.solidity_keccak(
                ['address', 'uint256', 'uint256', 'address'],
                [
                    self.student_address,
                    course_id,
                    teo_cost,
                    teocoin_discount_service.discount_contract.address
                ]
            )
            
            prefixed_hash = encode_defunct(message_hash)
            recovered_address = Account.recover_message(prefixed_hash, signature=signature.signature)
            
            if recovered_address.lower() == self.student_address.lower():
                self.log_test("Signature Verification", True, "Signature verification successful")
            else:
                self.log_test("Signature Verification", False, f"Expected {self.student_address}, got {recovered_address}")
            
            return True
            
        except Exception as e:
            self.log_test("Signature Flow", False, f"Error: {e}")
            return False
    
    def test_discount_request_creation(self):
        """Test 5: Create a discount request (if balances allow)"""
        print("\n📝 TEST 5: Discount Request Creation")
        print("-" * 50)
        
        if not self.student_account or not self.teacher_address:
            self.log_test("Discount Request", False, "Missing test accounts")
            return False
        
        try:
            # Check if student has enough TEO
            student_balance = self.teocoin_service.get_balance(self.student_address)
            required_teo = Decimal('50')  # 50 TEO for test
            
            if student_balance < required_teo:
                self.log_test("Discount Request", False, f"Insufficient TEO. Need {required_teo}, have {student_balance}")
                
                # Try to mint some TEO for testing
                print("🪙 Attempting to mint test TEO...")
                try:
                    mint_result = self.teocoin_service.mint_tokens(self.student_address, float(required_teo))
                    if mint_result:
                        self.log_test("Test TEO Minting", True, f"Minted {required_teo} TEO for testing")
                        student_balance = self.teocoin_service.get_balance(self.student_address)
                    else:
                        self.log_test("Test TEO Minting", False, "Minting failed")
                        return False
                except Exception as e:
                    self.log_test("Test TEO Minting", False, f"Minting error: {e}")
                    return False
            
            # Create a test discount request
            course_price = Decimal('100')  # €100 course
            discount_percent = 10  # 10% discount
            
            # Generate and sign request
            signature_data = teocoin_discount_service.generate_student_signature_data(
                self.student_address, 123, int(required_teo * 10**18)
            )
            
            signature = self.student_account.sign_message(signature_data['signable_message'])
            
            # Create request via service
            result = teocoin_discount_service.create_discount_request(
                student_address=self.student_address,
                teacher_address=self.teacher_address,
                course_id=123,
                course_price=course_price,
                discount_percent=discount_percent,
                student_signature=signature.signature.hex()
            )
            
            if result.get('success'):
                request_id = result.get('request_id')
                self.log_test("Discount Request Creation", True, f"Created request #{request_id}")
                return request_id
            else:
                self.log_test("Discount Request Creation", False, f"Error: {result.get('error')}")
                return False
            
        except Exception as e:
            self.log_test("Discount Request Creation", False, f"Error: {e}")
            return False
    
    def test_system_status(self):
        """Test 6: Overall system status"""
        print("\n🔍 TEST 6: System Status Check")
        print("-" * 50)
        
        try:
            # Check Web3 connection
            is_connected = self.w3.is_connected()
            self.log_test("Web3 Connection", is_connected, f"Connected: {is_connected}")
            
            # Check current block
            current_block = self.w3.eth.block_number
            self.log_test("Blockchain Sync", True, f"Current block: {current_block:,}")
            
            # Check gas price
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price, 'gwei')
            self.log_test("Network Gas Price", True, f"Gas price: {gas_price_gwei:.2f} Gwei")
            
            # Check platform account status (if configured)
            if teocoin_discount_service.platform_account:
                platform_balance = self.w3.eth.get_balance(teocoin_discount_service.platform_account.address)
                platform_balance_matic = self.w3.from_wei(platform_balance, 'ether')
                
                if platform_balance_matic > 0.1:
                    self.log_test("Platform Account", True, f"Balance: {platform_balance_matic:.4f} MATIC")
                else:
                    self.log_test("Platform Account", False, f"Low balance: {platform_balance_matic:.4f} MATIC")
            else:
                self.log_test("Platform Account", False, "Not configured")
            
            return True
            
        except Exception as e:
            self.log_test("System Status", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 TEOCOIN DISCOUNT SYSTEM - COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Network: Polygon Amoy")
        print(f"👤 Student: {self.student_address or 'Not configured'}")
        print(f"👨‍🏫 Teacher: {self.teacher_address or 'Not configured'}")
        
        # Run all tests
        tests = [
            self.test_contract_deployment,
            self.test_backend_service,
            self.test_account_balances,
            self.test_signature_flow,
            self.test_discount_request_creation,
            self.test_system_status
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_func.__name__, False, f"Unexpected error: {e}")
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        # Save results to file
        results_file = project_root / 'tests' / 'discount_system_test_results.json'
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! The discount system is ready for use! 🚀")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Please check the issues above.")


def main():
    """Main test execution"""
    print("🚀 Starting TeoCoin Discount System Tests...")
    
    # Check environment
    if not os.getenv('TEST_STUDENT_PRIVATE_KEY'):
        print("⚠️  WARNING: TEST_STUDENT_PRIVATE_KEY not set")
        print("   Set this environment variable to test with a real student account")
    
    if not os.getenv('TEST_TEACHER_PRIVATE_KEY'):
        print("⚠️  WARNING: TEST_TEACHER_PRIVATE_KEY not set")
        print("   Set this environment variable to test with a real teacher account")
    
    print("   You can still run basic tests without these accounts\n")
    
    # Run tests
    tester = DiscountSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
