# libvips Custom Build with AV2 (AVM) Support

This repository compiles libvips with native AV2/AVM decoding support for both Windows and Linux using GitHub Actions.

## Workflows

- **[Build libvips for Windows](.github/workflows/build-windows.yml)**: Builds DLLs using `build-win64-mxe`.
- **[Build libvips for Linux](.github/workflows/build-linux.yml)**: Builds shared libraries (.so) natively for Linux.
