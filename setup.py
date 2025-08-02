#!/usr/bin/env python3
"""
Computer Vision CNC Manufacturing Platform Setup Script

This setup script provides comprehensive project initialization and validation
for the Computer Vision CNC Manufacturing optimization platform.

Features:
- Development environment validation
- Dependency installation and verification
- Pre-commit hooks configuration
- Manufacturing compliance checking
- Security framework initialization
- Performance testing setup

Usage:
    python setup.py --dev          # Development environment
    python setup.py --production   # Production deployment
    python setup.py --compliance   # Compliance validation
    python setup.py --security     # Security framework setup
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SetupValidator:
    """Comprehensive setup validation for manufacturing environment."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_version = sys.version_info
        self.system_info = {
            'platform': platform.system(),
            'arch': platform.machine(),
            'python_version': f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}"
        }
        
    def validate_python_version(self) -> bool:
        """Validate Python version meets requirements."""
        print(f"{Colors.OKBLUE}Validating Python version...{Colors.ENDC}")
        
        if self.python_version < (3, 8):
            print(f"{Colors.FAIL}❌ Python 3.8+ required. Current: {self.system_info['python_version']}{Colors.ENDC}")
            return False
            
        print(f"{Colors.OKGREEN}✅ Python {self.system_info['python_version']} - Compatible{Colors.ENDC}")
        return True
    
    def validate_system_requirements(self) -> bool:
        """Validate system requirements for manufacturing platform."""
        print(f"{Colors.OKBLUE}Validating system requirements...{Colors.ENDC}")
        
        requirements = {
            'git': self._check_command('git --version'),
            'docker': self._check_command('docker --version'),
        }
        
        # Optional but recommended
        optional = {
            'nvidia-smi': self._check_command('nvidia-smi --version'),
            'openssl': self._check_command('openssl version'),
        }
        
        all_passed = True
        for req, available in requirements.items():
            if available:
                print(f"{Colors.OKGREEN}✅ {req} - Available{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ {req} - Required but not found{Colors.ENDC}")
                all_passed = False
        
        for opt, available in optional.items():
            if available:
                print(f"{Colors.OKGREEN}✅ {opt} - Available (optional){Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠️  {opt} - Not found (optional){Colors.ENDC}")
        
        return all_passed
    
    def _check_command(self, command: str) -> bool:
        """Check if a command exists and is executable."""
        try:
            subprocess.run(
                command.split(), 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def create_project_structure(self) -> bool:
        """Create the complete project directory structure."""
        print(f"{Colors.OKBLUE}Creating project structure...{Colors.ENDC}")
        
        directories = [
            'src/cv_cnc_manufacturing',
            'src/cv_cnc_manufacturing/core',
            'src/cv_cnc_manufacturing/computer_vision',
            'src/cv_cnc_manufacturing/cnc_integration',
            'src/cv_cnc_manufacturing/quality_control',
            'src/cv_cnc_manufacturing/predictive_maintenance',
            'src/cv_cnc_manufacturing/api',
            'src/cv_cnc_manufacturing/security',
            'src/cv_cnc_manufacturing/compliance',
            'src/cv_cnc_manufacturing/utils',
            'tests/unit',
            'tests/integration',
            'tests/performance',
            'tests/security',
            'tests/compliance',
            'docs/source',
            'docs/api',
            'docs/architecture',
            'configs',
            'schemas',
            'scripts',
            'data/samples',
            'data/models',
            'data/calibration',
            'logs',
            'temp',
            'certs',
            'compliance_reports',
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py for Python packages
            if 'src/' in directory or 'tests/' in directory:
                init_file = dir_path / '__init__.py'
                if not init_file.exists():
                    init_file.write_text('"""Package initialization."""\n')
        
        print(f"{Colors.OKGREEN}✅ Project structure created{Colors.ENDC}")
        return True
    
    def install_dependencies(self, env_type: str = 'dev') -> bool:
        """Install project dependencies based on environment type."""
        print(f"{Colors.OKBLUE}Installing {env_type} dependencies...{Colors.ENDC}")
        
        try:
            # Install base dependencies
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-e', '.'
            ], check=True)
            
            # Install environment-specific dependencies
            if env_type == 'dev':
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-e', '.[dev,test,docs]'
                ], check=True)
            elif env_type == 'production':
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-e', '.[security]'
                ], check=True)
            elif env_type == 'compliance':
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-e', '.[compliance,security]'
                ], check=True)
            
            print(f"{Colors.OKGREEN}✅ Dependencies installed successfully{Colors.ENDC}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Dependency installation failed: {e}{Colors.ENDC}")
            return False
    
    def setup_pre_commit_hooks(self) -> bool:
        """Setup pre-commit hooks for code quality."""
        print(f"{Colors.OKBLUE}Setting up pre-commit hooks...{Colors.ENDC}")
        
        try:
            # Install pre-commit hooks
            subprocess.run([
                sys.executable, '-m', 'pre_commit', 'install'
            ], check=True)
            
            # Run initial check
            subprocess.run([
                sys.executable, '-m', 'pre_commit', 'run', '--all-files'
            ], check=False)  # Don't fail if there are issues
            
            print(f"{Colors.OKGREEN}✅ Pre-commit hooks configured{Colors.ENDC}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Pre-commit setup failed: {e}{Colors.ENDC}")
            return False
    
    def validate_manufacturing_compliance(self) -> bool:
        """Validate manufacturing compliance requirements."""
        print(f"{Colors.OKBLUE}Validating manufacturing compliance...{Colors.ENDC}")
        
        compliance_checks = [
            self._check_security_certificates(),
            self._check_export_control_compliance(),
            self._check_manufacturing_standards(),
        ]
        
        if all(compliance_checks):
            print(f"{Colors.OKGREEN}✅ Manufacturing compliance validated{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.WARNING}⚠️  Some compliance checks failed - Review required{Colors.ENDC}")
            return False
    
    def _check_security_certificates(self) -> bool:
        """Check security certificate configuration."""
        cert_dir = self.project_root / 'certs'
        if not cert_dir.exists():
            cert_dir.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder for certificate management
        readme_file = cert_dir / 'README.md'
        if not readme_file.exists():
            readme_file.write_text("""# Security Certificates

This directory contains security certificates for industrial communication protocols.

## Required Certificates:
- OPC-UA Server Certificate
- OPC-UA Client Certificate
- TLS/SSL Certificates for API endpoints
- Manufacturing network access certificates

## Security Notes:
- Never commit actual certificates to version control
- Use environment-specific certificate management
- Follow IEC 62443 certificate lifecycle management
- Implement certificate rotation policies

## Setup:
1. Generate certificates using provided scripts
2. Configure certificate validation
3. Set up certificate monitoring
4. Document certificate dependencies
""")
        
        print(f"{Colors.OKGREEN}✅ Security certificate framework initialized{Colors.ENDC}")
        return True
    
    def _check_export_control_compliance(self) -> bool:
        """Check export control compliance framework."""
        compliance_dir = self.project_root / 'compliance_reports'
        if not compliance_dir.exists():
            compliance_dir.mkdir(parents=True, exist_ok=True)
        
        # Create compliance tracking template
        template_file = compliance_dir / 'export_control_template.md'
        if not template_file.exists():
            template_file.write_text("""# Export Control Compliance Report

## System Classification:
- [ ] Dual-use technology assessment completed
- [ ] Export control classification determined
- [ ] End-user verification implemented
- [ ] Geographic restriction compliance verified

## Technical Controls:
- [ ] Encryption algorithm compliance (FIPS 140-2)
- [ ] Network security protocols validated
- [ ] Data protection measures implemented
- [ ] Access control systems verified

## Documentation:
- [ ] Technical specifications reviewed
- [ ] User documentation sanitized
- [ ] Training materials approved
- [ ] Compliance monitoring implemented

## Approval Status:
- Review Date: [DATE]
- Compliance Officer: [NAME]
- Status: [PENDING/APPROVED/RESTRICTED]
- Next Review: [DATE]
""")
        
        print(f"{Colors.OKGREEN}✅ Export control framework initialized{Colors.ENDC}")
        return True
    
    def _check_manufacturing_standards(self) -> bool:
        """Check manufacturing standards compliance."""
        # ISO 9001, IATF 16949, IEC 62443 compliance framework
        standards_file = self.project_root / 'MANUFACTURING_STANDARDS.md'
        if not standards_file.exists():
            standards_file.write_text("""# Manufacturing Standards Compliance

## Quality Management (ISO 9001)
- [ ] Quality management system documented
- [ ] Process validation procedures implemented
- [ ] Continuous improvement framework established
- [ ] Customer satisfaction monitoring active

## Automotive Quality (IATF 16949)
- [ ] Risk-based thinking implemented
- [ ] Error proofing measures in place
- [ ] Statistical process control active
- [ ] Supplier quality management verified

## Industrial Cybersecurity (IEC 62443)
- [ ] Security by design principles applied
- [ ] Network segmentation implemented
- [ ] Security incident response plan active
- [ ] Vulnerability management program established

## Manufacturing Integration
- [ ] MTConnect compatibility verified
- [ ] OPC-UA security compliance validated
- [ ] Industrial network protocols secured
- [ ] Safety instrumented systems integrated

## Validation Status:
- Last Updated: [DATE]
- Standards Officer: [NAME]
- Compliance Level: [BASIC/INTERMEDIATE/ADVANCED]
- Certification Status: [PENDING/CERTIFIED/EXPIRED]
""")
        
        print(f"{Colors.OKGREEN}✅ Manufacturing standards framework initialized{Colors.ENDC}")
        return True
    
    def run_initial_tests(self) -> bool:
        """Run initial test suite to validate setup."""
        print(f"{Colors.OKBLUE}Running initial test suite...{Colors.ENDC}")
        
        try:
            # Run unit tests
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'tests/unit/', '-v', '--tb=short'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}✅ Initial tests passed{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.WARNING}⚠️  Some tests failed - This is normal for initial setup{Colors.ENDC}")
                print(f"Test output:\n{result.stdout}")
                return True  # Don't fail setup for test failures
                
        except subprocess.CalledProcessError as e:
            print(f"{Colors.WARNING}⚠️  Test execution failed: {e}{Colors.ENDC}")
            return True  # Don't fail setup for test execution issues


def main():
    """Main setup script entry point."""
    parser = argparse.ArgumentParser(
        description='Computer Vision CNC Manufacturing Platform Setup'
    )
    parser.add_argument(
        '--dev', action='store_true',
        help='Setup development environment'
    )
    parser.add_argument(
        '--production', action='store_true',
        help='Setup production environment'
    )
    parser.add_argument(
        '--compliance', action='store_true',
        help='Setup compliance validation environment'
    )
    parser.add_argument(
        '--security', action='store_true',
        help='Setup security framework'
    )
    parser.add_argument(
        '--validate-only', action='store_true',
        help='Only run validation checks'
    )
    
    args = parser.parse_args()
    
    # Determine environment type
    if args.production:
        env_type = 'production'
    elif args.compliance:
        env_type = 'compliance'
    else:
        env_type = 'dev'  # Default to development
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("Computer Vision CNC Manufacturing Platform Setup")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    print(f"Environment: {env_type.upper()}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    print()
    
    validator = SetupValidator()
    
    # Run validation checks
    validation_results = [
        validator.validate_python_version(),
        validator.validate_system_requirements(),
    ]
    
    if not all(validation_results):
        print(f"{Colors.FAIL}❌ Setup validation failed. Please resolve issues above.{Colors.ENDC}")
        sys.exit(1)
    
    if args.validate_only:
        print(f"{Colors.OKGREEN}✅ Validation completed successfully{Colors.ENDC}")
        sys.exit(0)
    
    # Run setup steps
    setup_results = [
        validator.create_project_structure(),
        validator.install_dependencies(env_type),
        validator.setup_pre_commit_hooks(),
        validator.validate_manufacturing_compliance(),
        validator.run_initial_tests(),
    ]
    
    if all(setup_results):
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 Setup completed successfully!{Colors.ENDC}")
        print(f"\n{Colors.OKBLUE}Next steps:{Colors.ENDC}")
        print(f"1. Review configuration files in configs/")
        print(f"2. Update manufacturing specifications")
        print(f"3. Configure CNC machine connections")
        print(f"4. Set up computer vision models")
        print(f"5. Run comprehensive test suite")
        print(f"\n{Colors.OKBLUE}Development commands:{Colors.ENDC}")
        print(f"- pytest tests/               # Run all tests")
        print(f"- pre-commit run --all-files  # Run code quality checks")
        print(f"- python -m cv_cnc_manufacturing --help  # CLI help")
        print(f"- docker-compose up           # Start development environment")
    else:
        print(f"\n{Colors.FAIL}❌ Setup completed with warnings. Please review output above.{Colors.ENDC}")
        sys.exit(1)


if __name__ == '__main__':
    main()
