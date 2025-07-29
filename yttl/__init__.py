# SPDX-License-Identifier: Apache-2.0

def cli_main():
    from .cli import main
    main()

def extension_main():
    from .extension import main
    main()

# Export main functions for programmatic use
from .yttl import process_video, load_config
