# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags configured in the
# default ProGuard configuration file.

# Uncomment this to preserve the line number information for
# debugging stack traces.
# -keepattributes SourceFile,LineNumberTable

# If you keep the line number information, uncomment this to
# hide the original source file name.
# -renamesourcefileattribute SourceFile

# Retrofit
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn javax.annotation.**
-keep class retrofit2.** { *; }
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations

# Coroutines
-keepclassmembernames class kotlinx.coroutines.internal.MainDispatcherFactory[] {
    <fields>;
}
