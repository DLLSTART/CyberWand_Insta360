# Append -Wno-error at the very end of compile options
# This must run AFTER ESP-IDF adds its -Werror
idf_build_set_property(COMPILE_OPTIONS "-Wno-error" APPEND)
idf_build_set_property(COMPILE_OPTIONS "-Wno-unknown-pragmas" APPEND)