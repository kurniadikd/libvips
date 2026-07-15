import pathlib

content = r'''name: Build libvips

on:
  schedule:
    - cron: '0 0 * * *' # Runs automatically every day at 00:00 UTC
  workflow_dispatch:
  push:
    branches: [ main ]

permissions:
  contents: write

jobs:
  build-windows:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y curl sed jq python3

      - name: Clone libvips/build-win64-mxe
        run: |
          git clone https://github.com/libvips/build-win64-mxe.git
          cd build-win64-mxe
          git checkout master

      - name: Fetch and calculate checksums for dependencies
        id: checksums
        run: |
          # vvdec (VVC Decoder)
          VVDEC_TAG=$(curl -s "https://api.github.com/repos/fraunhoferhhi/vvdec/releases/latest" | jq -r .tag_name)
          VVDEC_VERSION=${VVDEC_TAG#v}
          echo "Fetching vvdec version: ${VVDEC_VERSION}"
          curl -L -o vvdec.tar.gz "https://github.com/fraunhoferhhi/vvdec/archive/refs/tags/v${VVDEC_VERSION}.tar.gz"
          VVDEC_CHECKSUM=$(sha256sum vvdec.tar.gz | awk '{print $1}')
          echo "vvdec_checksum=${VVDEC_CHECKSUM}" >> $GITHUB_OUTPUT
          echo "vvdec_version=${VVDEC_VERSION}" >> $GITHUB_OUTPUT
          
          # vvenc (VVC Encoder)
          VVENC_TAG=$(curl -s "https://api.github.com/repos/fraunhoferhhi/vvenc/releases/latest" | jq -r .tag_name)
          VVENC_VERSION=${VVENC_TAG#v}
          echo "Fetching vvenc version: ${VVENC_VERSION}"
          curl -L -o vvenc.tar.gz "https://github.com/fraunhoferhhi/vvenc/archive/refs/tags/v${VVENC_VERSION}.tar.gz"
          VVENC_CHECKSUM=$(sha256sum vvenc.tar.gz | awk '{print $1}')
          echo "vvenc_checksum=${VVENC_CHECKSUM}" >> $GITHUB_OUTPUT
          echo "vvenc_version=${VVENC_VERSION}" >> $GITHUB_OUTPUT

          # SVT-AV1 (AV1 Encoder)
          SVT_TAG=$(curl -s "https://gitlab.com/api/v4/projects/AOMediaCodec%2FSVT-AV1/releases" | jq -r '.[0].tag_name')
          SVT_VERSION=${SVT_TAG#v}
          echo "Fetching SVT-AV1 version: ${SVT_VERSION}"
          curl -L -o svt.tar.gz "https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v${SVT_VERSION}/SVT-AV1-v${SVT_VERSION}.tar.gz"
          SVT_CHECKSUM=$(sha256sum svt.tar.gz | awk '{print $1}')
          echo "svt_checksum=${SVT_CHECKSUM}" >> $GITHUB_OUTPUT
          echo "svt_version=${SVT_VERSION}" >> $GITHUB_OUTPUT

          # libvips (Image Processing Library)
          VIPS_TAG=$(curl -s "https://api.github.com/repos/libvips/libvips/releases/latest" | jq -r .tag_name)
          VIPS_VERSION=${VIPS_TAG#v}
          echo "Fetching latest libvips version: ${VIPS_VERSION}"
          curl -L -o vips.tar.xz "https://github.com/libvips/libvips/releases/download/v${VIPS_VERSION}/vips-${VIPS_VERSION}.tar.xz"
          VIPS_CHECKSUM=$(sha256sum vips.tar.xz | awk '{print $1}')
          echo "vips_checksum=${VIPS_CHECKSUM}" >> $GITHUB_OUTPUT
          echo "vips_version=${VIPS_VERSION}" >> $GITHUB_OUTPUT

      - name: Add vvdec, vvenc and svt MXE recipes
        run: |
          cd build-win64-mxe
          python3 - << 'EOF'
          import textwrap

          vvdec_content = textwrap.dedent("""\
              PKG             := vvdec
              $(PKG)_WEBSITE  := https://github.com/fraunhoferhhi/vvdec
              $(PKG)_DESCR    := Fraunhofer HHI VVC Decoder
              $(PKG)_IGNORE   :=
              $(PKG)_VERSION  := ${{ steps.checksums.outputs.vvdec_version }}
              $(PKG)_CHECKSUM := ${{ steps.checksums.outputs.vvdec_checksum }}
              $(PKG)_PATCHES  :=
              $(PKG)_SUBDIR   := vvdec-$($(PKG)_VERSION)
              $(PKG)_FILE     := vvdec-$($(PKG)_VERSION).tar.gz
              $(PKG)_URL      := https://github.com/fraunhoferhhi/vvdec/archive/refs/tags/v$($(PKG)_VERSION).tar.gz
              $(PKG)_DEPS     := cc

              define $(PKG)_BUILD
                   cd '$(BUILD_DIR)' && $(TARGET)-cmake \\
                       -DBUILD_SHARED_LIBS=OFF \\
                       -DCONFIG_PIC=ON \\
                       -DVVDEC_ENABLE_WARNINGS_AS_WERROR=OFF \\
                       -DVVDEC_ENABLE_LINK_TIME_OPT=OFF \\
                       '$(SOURCE_DIR)'
                   $(MAKE) -C '$(BUILD_DIR)' -j '$(JOBS)'
                   $(MAKE) -C '$(BUILD_DIR)' -j 1 $(subst -,/,$(INSTALL_STRIP_LIB))
              endef
          """)
          with open("build/vvdec.mk", "w") as f:
              f.write(vvdec_content)

          vvenc_content = textwrap.dedent("""\
              PKG             := vvenc
              $(PKG)_WEBSITE  := https://github.com/fraunhoferhhi/vvenc
              $(PKG)_DESCR    := Fraunhofer HHI VVC Encoder
              $(PKG)_IGNORE   :=
              $(PKG)_VERSION  := ${{ steps.checksums.outputs.vvenc_version }}
              $(PKG)_CHECKSUM := ${{ steps.checksums.outputs.vvenc_checksum }}
              $(PKG)_PATCHES  :=
              $(PKG)_SUBDIR   := vvenc-$($(PKG)_VERSION)
              $(PKG)_FILE     := vvenc-$($(PKG)_VERSION).tar.gz
              $(PKG)_URL      := https://github.com/fraunhoferhhi/vvenc/archive/refs/tags/v$($(PKG)_VERSION).tar.gz
              $(PKG)_DEPS     := cc

              define $(PKG)_BUILD
                   cd '$(BUILD_DIR)' && $(TARGET)-cmake \\
                       -DBUILD_SHARED_LIBS=OFF \\
                       -DCONFIG_PIC=ON \\
                       -DVVENC_ENABLE_WERROR=OFF \\
                       -DVVENC_ENABLE_LINK_TIME_OPT=OFF \\
                       '$(SOURCE_DIR)'
                   $(MAKE) -C '$(BUILD_DIR)' -j '$(JOBS)'
                   $(MAKE) -C '$(BUILD_DIR)' -j 1 $(subst -,/,$(INSTALL_STRIP_LIB))
              endef
          """)
          with open("build/vvenc.mk", "w") as f:
              f.write(vvenc_content)

          svt_content = textwrap.dedent("""\
              PKG             := svt
              $(PKG)_WEBSITE  := https://gitlab.com/AOMediaCodec/SVT-AV1
              $(PKG)_DESCR    := Scalable Video Technology for AV1
              $(PKG)_IGNORE   :=
              $(PKG)_VERSION  := ${{ steps.checksums.outputs.svt_version }}
              $(PKG)_CHECKSUM := ${{ steps.checksums.outputs.svt_checksum }}
              $(PKG)_PATCHES  :=
              $(PKG)_SUBDIR   := SVT-AV1-v$($(PKG)_VERSION)
              $(PKG)_FILE     := SVT-AV1-v$($(PKG)_VERSION).tar.gz
              $(PKG)_URL      := https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v$($(PKG)_VERSION)/$($(PKG)_FILE)
              $(PKG)_DEPS     := cc $(BUILD)~nasm

              define $(PKG)_BUILD
                  cd '$(BUILD_DIR)' && $(TARGET)-cmake \\
                      -DBUILD_SHARED_LIBS=OFF \\
                      -DCONFIG_PIC=ON \\
                      -DENABLE_AVX512=OFF \\
                      -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF \\
                      -DENABLE_LTO=OFF \\
                      '$(SOURCE_DIR)'
                  $(MAKE) -C '$(BUILD_DIR)' -j '$(JOBS)'
                  $(MAKE) -C '$(BUILD_DIR)' -j 1 $(subst -,/,$(INSTALL_STRIP_LIB))
              endef
          """)
          with open("build/svt.mk", "w") as f:
              f.write(svt_content)
          EOF

      - name: Patch libheif, vips-web and vips recipes for VVC, SVT, JXL and latest version support
        run: |
          cd build-win64-mxe
          python3 -c '
          # 1. Patch libheif
          with open("build/libheif.mk", "r") as f:
              content = f.read()
          content = content.replace("$(PKG)_DEPS     := cc aom", "$(PKG)_DEPS     := cc aom svt vvdec vvenc")
          content = content.replace(
              "-DENABLE_PLUGIN_LOADING=0 \\",
              "-DENABLE_PLUGIN_LOADING=0 \\\n        -DWITH_VVDEC=ON \\\n        -DWITH_VVENC=ON \\\n        -DWITH_SvtEnc=ON \\"
          )
          content = content.replace(
              "$(MAKE) -C '"'"'$(BUILD_DIR)'"'"' -j 1 $(subst -,/,$(INSTALL_STRIP_LIB))",
              "$(MAKE) -C '"'"'$(BUILD_DIR)'"'"' -j 1 $(subst -,/,$(INSTALL_STRIP_LIB))\n" +
              "\techo \"Libs.private: -lvvenc -lvvdec -lSvtAv1Enc\" >> '"'"'$(PREFIX)/$(TARGET)/lib/pkgconfig/libheif.pc'"'"'"
          )
          with open("build/libheif.mk", "w") as f:
              f.write(content)

          # 2. Patch vips-web to include libjxl
          with open("build/plugins/web-deps/vips-web.mk", "r") as f:
              web_content = f.read()
          web_content = web_content.replace(
              "$(PKG)_DEPS     := $(vips_DEPS)",
              "$(PKG)_DEPS     := $(vips_DEPS) libjxl"
          )
          web_content = web_content.replace(
              "printf '\''  \"lcms\": \"$(lcms_VERSION)\",\\n'\''; \\",
              "printf '\''  \"jxl\": \"$(libjxl_VERSION)\",\\n'\''; \\\n     printf '\''  \"lcms\": \"$(lcms_VERSION)\",\\n'\''; \\"
          )
          with open("build/plugins/web-deps/vips-web.mk", "w") as f:
              f.write(web_content)

          # 3. Patch vips.mk to use the latest version and checksum
          with open("build/vips.mk", "r") as f:
              vips_content = f.read()
          import re
          vips_content = re.sub(r"\$\(PKG\)_VERSION  := .*", "$(PKG)_VERSION  := ${{ steps.checksums.outputs.vips_version }}", vips_content)
          vips_content = re.sub(r"\$\(PKG\)_CHECKSUM := .*", "$(PKG)_CHECKSUM := ${{ steps.checksums.outputs.vips_checksum }}", vips_content)
          with open("build/vips.mk", "w") as f:
              f.write(vips_content)

          # 4. Patch overrides.mk to enable JXL in meson options
          with open("build/plugins/web-deps/overrides.mk", "r") as f:
              overrides_content = f.read()
          overrides_content = overrides_content.replace(
              "-Djpeg-xl=disabled",
              "-Djpeg-xl=enabled"
          )
          with open("build/plugins/web-deps/overrides.mk", "w") as f:
              f.write(overrides_content)
          '
          echo "=== Modified build/libheif.mk ==="
          cat build/libheif.mk
          echo "=== Modified build/plugins/web-deps/vips-web.mk ==="
          cat build/plugins/web-deps/vips-web.mk
          echo "=== Modified build/vips.mk ==="
          cat build/vips.mk
          echo "=== Modified build/plugins/web-deps/overrides.mk ==="
          cat build/plugins/web-deps/overrides.mk

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build libvips using MXE
        run: |
          cd build-win64-mxe
          ./build.sh -t x86_64-w64-mingw32.shared vips-web --with-jpegli

      - name: Verify build outputs and codec support
        run: |
          cd build-win64-mxe/packaging
          unzip vips-dev-*.zip -d test-vips
          # 1. Verify critical codec DLLs exist in the package
          find test-vips -name "libjxl.dll" | grep "libjxl.dll" || (echo "ERROR: libjxl.dll not found!" && exit 1)
          find test-vips -name "libheif.dll" | grep "libheif.dll" || (echo "ERROR: libheif.dll not found!" && exit 1)
          find test-vips -name "libwebp*.dll" | grep -E "libwebp" || (echo "ERROR: libwebp DLL not found!" && exit 1)
          find test-vips -name "libjpeg*.dll" | grep -E "libjpeg" || (echo "ERROR: libjpeg DLL not found!" && exit 1)
          # 2. Verify with Wine if available
          if command -v wine64 &> /dev/null; then
            echo "Running vips.exe -l under Wine..."
            WINEDEBUG=-all wine64 test-vips/vips-dev-*/bin/vips.exe -l | grep jxl || (echo "ERROR: JXL not registered in vips!" && exit 1)
            WINEDEBUG=-all wine64 test-vips/vips-dev-*/bin/vips.exe -l | grep heif || (echo "ERROR: HEIF not registered in vips!" && exit 1)
            WINEDEBUG=-all wine64 test-vips/vips-dev-*/bin/vips.exe -l | grep webp || (echo "ERROR: WEBP not registered in vips!" && exit 1)
            WINEDEBUG=-all wine64 test-vips/vips-dev-*/bin/vips.exe -l | grep jpeg || (echo "ERROR: JPEG not registered in vips!" && exit 1)
            WINEDEBUG=-all wine64 test-vips/vips-dev-*/bin/vips.exe -l | grep png || (echo "ERROR: PNG not registered in vips!" && exit 1)
          elif command -v wine &> /dev/null; then
            echo "Running vips.exe -l under Wine..."
            WINEDEBUG=-all wine test-vips/vips-dev-*/bin/vips.exe -l | grep jxl || (echo "ERROR: JXL not registered in vips!" && exit 1)
            WINEDEBUG=-all wine test-vips/vips-dev-*/bin/vips.exe -l | grep heif || (echo "ERROR: HEIF not registered in vips!" && exit 1)
            WINEDEBUG=-all wine test-vips/vips-dev-*/bin/vips.exe -l | grep webp || (echo "ERROR: WEBP not registered in vips!" && exit 1)
            WINEDEBUG=-all wine test-vips/vips-dev-*/bin/vips.exe -l | grep jpeg || (echo "ERROR: JPEG not registered in vips!" && exit 1)
            WINEDEBUG=-all wine test-vips/vips-dev-*/bin/vips.exe -l | grep png || (echo "ERROR: PNG not registered in vips!" && exit 1)
          else
            echo "Wine not found, skipping runtime check."
          fi

      - name: Upload Build Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: libvips-windows
          path: build-win64-mxe/packaging/*.zip

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
          files: build-win64-mxe/packaging/*.zip

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
          if [ -n "$AOM_CONFIG_PATH" ]; then
            echo "Found aom_config.h at: ${AOM_CONFIG_PATH}"
            sudo mkdir -p /usr/local/avm/include/aom/config
            sudo cp "${AOM_CONFIG_PATH}" /usr/local/avm/include/aom/config/aom_config.h
            sudo cp "${AOM_CONFIG_PATH}" /usr/local/avm/include/aom/aom_config.h
          else
            echo "aom_config.h not found, skipping header copy."
          fi
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
          mkdir build_dir && cd build_dir
          export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
          cmake -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_SHARED_LIBS=ON \
            -DENABLE_PLUGIN_LOADING=OFF \
            -DWITH_VVDEC=ON \
            -DWITH_VVENC=ON \
            -DWITH_EXAMPLES=OFF \
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
'''

pathlib.Path('.github/workflows/build.yml').write_text(content.replace('\r\n', '\n'), encoding='utf-8')
print('Done')
