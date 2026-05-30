"""
PlatformIO extra script: forcefully add -Wno-error after ALL other compile flags.
ESP-IDF 6.0.1 on PlatformIO 7.0.1 adds -Werror after project flags.
We intercept at the SCons builder level to ensure -Wno-error is the LAST flag.
"""
from SCons.Script import Import

Import("env")

# Store original builders
orig_cccom = env.get('CCCOM', '')
orig_cxxcom = env.get('CXXCOM', '')

# Force -Wno-error at the very end of all compile commands
# by appending directly to the command strings
if orig_cccom:
    env['CCCOM'] = orig_cccom.replace('${_COMPILE}', '${_COMPILE} -Wno-error')
if orig_cxxcom:
    env['CXXCOM'] = orig_cxxcom.replace('${_COMPILE}', '${_COMPILE} -Wno-error')

# Also try the simpler Append approach
env.Append(CCFLAGS=['-Wno-error'])
env.Append(CFLAGS=['-Wno-error'])
env.Append(CXXFLAGS=['-Wno-error'])

print("[patch_werror] SCons environment patched")