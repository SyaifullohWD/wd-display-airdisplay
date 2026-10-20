plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

// Fixed audit-fix identity; explicit CI overrides remain reproducible (no clock/git state).
val padVersionName = providers.environmentVariable("PAD_VERSION_NAME").orElse("0.1.2-dev").get()
val padVersionCode = providers.environmentVariable("PAD_VERSION_CODE").orElse("3").get().toInt()
// Release signing: CI decodes the keystore from repository secrets. Without it, release APKs are unsigned.
val padKeystorePath = providers.environmentVariable("PAD_KEYSTORE_PATH").orNull?.takeIf { it.isNotEmpty() }

android {
    namespace = "org.pocketairdisplay.receiver"
    compileSdk = 36
    buildToolsVersion = "36.0.0"
    ndkVersion = "27.3.13750724"
    val bundledNdk = File(rootDir, ".tools/ndk-r27d")
    if (bundledNdk.isDirectory) {
        ndkPath = bundledNdk.absolutePath
    }
    signingConfigs {
        if (padKeystorePath != null) {
            fun signingEnv(name: String): String =
                providers.environmentVariable(name).orNull?.takeIf { it.isNotEmpty() }
                    ?: throw GradleException("PAD_KEYSTORE_PATH is set but $name is missing; set all release signing variables")
            create("release") {
                storeFile = file(padKeystorePath)
                storePassword = signingEnv("PAD_KEYSTORE_PASSWORD")
                keyAlias = signingEnv("PAD_KEY_ALIAS")
                keyPassword = signingEnv("PAD_KEY_PASSWORD")
            }
        }
    }
    defaultConfig {
        // New install identity for the WD Display branding. The Kotlin/JNI package
        // (namespace) stays org.pocketairdisplay.receiver so native symbol names and
        // the receiver core are unchanged; only the app id moved, which also gives
        // launchers a clean icon entry instead of a stale cached bitmap.
        applicationId = "org.wddisplay.receiver"
        // Deps in app/src/main/cpp/deps were built with __ANDROID_API__=29, so
        // minSdk is 29 (Android 10) to match what the shipped binaries support.
        minSdk = 29
        targetSdk = 34
        versionCode = padVersionCode
        versionName = padVersionName
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk { abiFilters += "arm64-v8a" }
        externalNativeBuild {
            cmake {
                targets("pocketairdisplay")
                // NDK r27 requires opt-in for 16 KiB ELF LOAD alignment.
                arguments += "-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON"
            }
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.findByName("release")
        }
    }
    externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt") } }
    lint {
        // targetSdk 34: general Android phones; APKs sideloaded, not Play Store.
        // Keep the Play-policy check visible as a warning instead of failing release builds.
        warning += "ExpiredTargetSdkVersion"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.04.01"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test:core:1.6.1")
    androidTestImplementation("junit:junit:4.13.2")
}
