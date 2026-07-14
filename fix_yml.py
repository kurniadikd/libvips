import pathlib
content = """name: Build libvips for Linux

on:
  schedule:
    - cron: '0 1 * * *' # Runs automatically every day at 01:00 UTC
  workflow_dispatch:
  push:
    branches: [ main ]

permissions:
  contents: write

jobs:
  build-linux:
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Install Build Dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            build-essential \
            cmake \
            ninja-build \
            meson \
            pkg-config \
            nasm \
            yasm \
            gcc-13 \
            g++-13 \
            libglib2.0-dev \
            libexpat1-dev \
            libpng-dev \
            libjpeg-turbo8-dev \
            libwebp-dev \
            libzstd-dev \
            libde265-dev \
            libgif-dev \
            libbrotli-dev

      - name: Compile Standard libaom (AV1 Support)
        run: |
          git clone https://aomedia.googlesource.com/aom
          cd aom
          git checkout $(git tag -l "v[0-9]*" | sort -V | tail -n 1)
          mkdir build_dir && cd build_dir
          cmake -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=0 \
            -DCONFIG_PIC=1 \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DCMAKE_INSTALL_LIBDIR=lib \
            ..
          ninja
          sudo ninja install
          cd ../..

      - name: Compile AVM (AV2 Reference Software - Isolated)
        run: |
          git clone https://github.com/AOMediaCodec/avm.git
          cd avm
          git checkout $(git tag -l "research-v[0-9]*" | sort -V | tail -n 1)
          mkdir build_dir && cd build_dir
          cmake -G Ninja \
            -DCMAKE_C_COMPILER=gcc-13 \
            -DCMAKE_CXX_COMPILER=g++-13 \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=0 \
            -DCONFIG_PIC=1 \
            -DENABLE_WERROR=0 \
            -DCMAKE_C_FLAGS="-w" \
            -DCMAKE_CXX_FLAGS="-w" \
            -DENABLE_DOCS=0 \
            -DENABLE_EXAMPLES=0 \
            -DENABLE_TESTS=0 \
            -DENABLE_TOOLS=0 \
            -DCMAKE_INSTALL_PREFIX=/usr/local/avm \
            ..
          ninja
          sudo ninja install
          AOM_CONFIG_PATH=$(find . -name "aom_config.h" | head -n 1)
          echo "Found aom_config.h at: ${AOM_CONFIG_PATH}"
          sudo cp "${AOM_CONFIG_PATH}" /usr/local/avm/include/aom/config/aom_config.h
          sudo cp "${AOM_CONFIG_PATH}" /usr/local/avm/include/aom/aom_config.h
          cd ../..

      - name: Compile vvdec (VVC Decoder)
        run: |
          git clone https://github.com/fraunhoferhhi/vvdec.git
          cd vvdec
          git checkout $(git tag -l "v[0-9]*" | sort -V | tail -n 1)
          mkdir build_dir && cd build_dir
          cmake -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=0 \
            -DCONFIG_PIC=1 \
            -DVVDEC_ENABLE_WARNINGS_AS_WERROR=OFF \
            -DVVDEC_ENABLE_LINK_TIME_OPT=OFF \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DCMAKE_INSTALL_LIBDIR=lib \
            ..
          ninja
          sudo ninja install
          cd ../..

      - name: Compile vvenc (VVC Encoder)
        run: |
          git clone https://github.com/fraunhoferhhi/vvenc.git
          cd vvenc
          git checkout $(git tag -l "v[0-9]*" | sort -V | tail -n 1)
          mkdir build_dir && cd build_dir
          cmake -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=0 \
            -DCONFIG_PIC=1 \
            -DVVENC_ENABLE_WERROR=OFF \
            -DVVENC_ENABLE_LINK_TIME_OPT=OFF \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DCMAKE_INSTALL_LIBDIR=lib \
            ..
          ninja
          sudo ninja install
          cd ../..

      - name: Compile Jpegli (via libjxl)
        run: |
          git clone --recursive https://github.com/libjxl/libjxl.git
          cd libjxl
          git checkout $(git tag -l "v[0-9]*" | sort -V | tail -n 1)
          git submodule update --init --recursive --jobs 8
          mkdir build && cd build
          cmake -G Ninja .. \
            -DCMAKE_BUILD_TYPE=Release \
            -DJPEGXL_INSTALL_JPEGLI_LIBJPEG=ON \
            -DJPEGLI_LIBJPEG_LIBRARY_VERSION=8.2.2 \
            -DJPEGLI_LIBJPEG_LIBRARY_SOVERSION=8 \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DCMAKE_INSTALL_LIBDIR=lib
          ninja
          sudo ninja install
          sudo ldconfig
          cd ../..

      - name: Compile libheif with AV1 and VVC
        run: |
          git clone https://github.com/strukturag/libheif.git
          cd libheif
          git checkout $(git tag -l "v[0-9]*" | sort -V | tail -n 1)
          
          # Fix: Jpegli defines LIBJPEG_TURBO_VERSION_NUMBER empty, breaking example tools
          sed -i 's/defined(LIBJPEG_TURBO_VERSION_NUMBER) && LIBJPEG_TURBO_VERSION_NUMBER == 2000000/0/g' examples/decoder_jpeg.cc
          
          mkdir build_dir && cd build_dir
          export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
          cmake -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=ON \
            -DENABLE_PLUGIN_LOADING=OFF \
            -DWITH_VVDEC=ON \
            -DWITH_VVENC=ON \
            -DCMAKE_INSTALL_PREFIX=/usr/local \
            -DCMAKE_INSTALL_LIBDIR=lib \
            ..
          ninja
          sudo ninja install
          cd ../..

      - name: Compile libvips with custom libheif
        run: |
          git clone https://github.com/libvips/libvips.git
          cd libvips
          git checkout $(git tag -l "v[0-9]*" | sort -V | tail -n 1)
          export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
          export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
          sudo apt-get remove -y libjpeg-turbo8-dev libjpeg-dev || true
          meson setup build_dir \
            --buildtype=release \
            --prefix=/usr/local \
            --libdir=lib \
            -Dpdfium=disabled
          cd build_dir
          ninja
          sudo ninja install
          cd ../..

      - name: Bundle and Package libvips Linux binaries
        run: |
          mkdir -p dist/lib dist/include dist/av2
          
          # Copy libraries from either /usr/local/lib/x86_64-linux-gnu or /usr/local/lib
          for libdir in /usr/local/lib/x86_64-linux-gnu /usr/local/lib; do
            if [ -d "$libdir" ]; then
              cp -d "$libdir"/libvips.so* dist/lib/ 2>/dev/null || true
              cp -d "$libdir"/libheif.so* dist/lib/ 2>/dev/null || true
              cp -d "$libdir"/libjpeg.so* dist/lib/ 2>/dev/null || true
              cp -d "$libdir"/libjxl.so* dist/lib/ 2>/dev/null || true
              cp -d "$libdir"/libjxl_threads.so* dist/lib/ 2>/dev/null || true
              cp -d "$libdir"/libjxl_cms.so* dist/lib/ 2>/dev/null || true
            fi
          done
          
          # Verify critical libraries exist in dist/lib
          if [ ! -f dist/lib/libvips.so ] && [ -z "$(ls dist/lib/libvips.so* 2>/dev/null)" ]; then
            echo "Error: libvips.so not found in dist/lib"
            exit 1
          fi
          if [ ! -f dist/lib/libheif.so ] && [ -z "$(ls dist/lib/libheif.so* 2>/dev/null)" ]; then
            echo "Error: libheif.so not found in dist/lib"
            exit 1
          fi
          if [ ! -f dist/lib/libjxl.so ] && [ -z "$(ls dist/lib/libjxl.so* 2>/dev/null)" ]; then
            echo "Error: libjxl.so not found in dist/lib"
            exit 1
          fi
          if [ ! -f dist/lib/libjpeg.so ] && [ -z "$(ls dist/lib/libjpeg.so* 2>/dev/null)" ]; then
            echo "Error: libjpeg.so not found in dist/lib"
            exit 1
          fi
          
          cp -r /usr/local/include/vips dist/include/
          cp -r /usr/local/avm/* dist/av2/ || true
          tar -czf libvips-linux.tar.gz dist/

      - name: Upload Build Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: libvips-linux
          path: libvips-linux.tar.gz

      - name: Create or Update Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: latest
          name: Latest Automated Build
          body: |
            Automated builds of libvips for Windows and Linux.
            Updated automatically.
          draft: false
          prerelease: false
          files: libvips-linux.tar.gz
"""
pathlib.Path('.github/workflows/build-linux.yml').write_text(content.replace('\r\n', '\n'), encoding='utf-8')
print('Done')
