plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val udpKeySourceFile = rootProject.file("../desktop/udp.key")
val udpKeyAssetFile = layout.projectDirectory.file("src/main/assets/udp.key")

tasks.register("syncUdpKeyAsset") {
    group = "build setup"
    description = "Copies desktop udp.key into app assets when available."
    doLast {
        val destination = udpKeyAssetFile.asFile
        if (udpKeySourceFile.exists()) {
            destination.parentFile.mkdirs()
            udpKeySourceFile.copyTo(destination, overwrite = true)
        } else if (destination.exists()) {
            destination.delete()
        }
    }
}

tasks.named("preBuild").configure {
    dependsOn("syncUdpKeyAsset")
}

android {
    namespace = "com.robocart.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.robocart.app"
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation(project(":data"))
    implementation(project(":domain"))
    implementation(project(":presentation"))

    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.3")
    implementation("androidx.appcompat:appcompat:1.7.0")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
