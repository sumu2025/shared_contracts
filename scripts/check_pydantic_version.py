#!/usr/bin/env python3
"""检查Pydantic版本是否符合要求。"""

import sys
import pydantic

def main():
    """主函数，检查Pydantic版本是否至少为2.0。"""
    print(f'Pydantic version: {pydantic.__version__}')
    
    version_major = int(pydantic.__version__.split('.')[0])
    if version_major < 2:
        print('Error: Pydantic version must be >= 2.0')
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
