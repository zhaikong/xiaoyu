# iOS 未签名 IPA

[返回 README](../README.md) · [Android 发布](ANDROID_RELEASE.md)

## GitHub 自动构建

统一工作流 [Mobile release](../.github/workflows/android-release.yml) 在推送 `main` 或手动触发时同时构建 Android APK 和未签名 IPA，发布到同一个 GitHub Release。macOS 15 使用 Flutter 3.50.0、Swift Package Manager 和完整 Agora 依赖构建真机 ARM64 Release 应用，不需要 Apple 证书、描述文件或 App Store Connect 密钥。

构建命令为 `flutter build ios --release --no-codesign`。Flutter 的 IPA 导出需要签名，关闭签名会跳过导出，因此使用 [package_unsigned_ipa.py](../tool/ci/package_unsigned_ipa.py) 将 `build/ios/iphoneos/Runner.app` 封装为 `Payload/Runner.app`。打包器拒绝模拟器、缺少可执行文件、主应用已包含签名或描述文件的产物，保留可执行权限及框架符号链接。CI 使用 `xcrun lipo build/ios/iphoneos/Runner.app/Runner -verify_arch arm64` 确认主可执行文件含 ARM64 架构；输入文件放在命令选项之前。

格式、静态分析、CI 辅助脚本和逻辑测试在共享任务执行；Android 与 iOS 构建随后并行。两端构建、校验和封装都成功后，由唯一的 Ubuntu 发布任务上传到同一 GitHub 预发布版本，任一端失败则不执行发布。GitHub Actions 不运行 UI、布局或黄金图测试；完整 Harness/UI 验证保留在本地。工作流不读取设备配置或创建真实收费通话。

共享标签为 `v<版本>-build.<运行编号>`；IPA 附件名为 `xiaoyu-<标签>-unsigned.ipa`，APK 名为 `xiaoyu-<标签>-arm64-v8a.apk`，共同提供一份 `SHA256SUMS.txt`。构建号为 `1000 + GITHUB_RUN_NUMBER`。Actions 产物保留 14 天，GitHub Release 附件独立保留。同一运行重试复用标签，新提交取消同分支旧构建。

## 下载和安装

在 [GitHub Releases](https://github.com/hsuehly/xiaoyu/releases) 在同一个 Android / iOS 预发布版本下下载文件名含 `-unsigned.ipa` 的附件。此文件需要自行重新签名后安装，不是可直接安装的签名包，也不能直接提交到 TestFlight 或 App Store。

最低系统为 iOS 15。重签工具需要为主应用及嵌入框架使用有效签名，并匹配自己的 Bundle ID、描述文件和权限。安装期限及允许的设备取决于所用签名。重签后须验证安全存储、麦克风授权和实际音视频通话；自动构建通过不代表这些设备行为已验收。
