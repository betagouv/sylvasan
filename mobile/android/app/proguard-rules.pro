# Conserver les numéros de ligne et fichiers source pour les rapports Sentry
-keepattributes LineNumberTable,SourceFile
-renamesourcefileattribute SourceFile

# Capacitor : conserver les plugins et leurs méthodes annotées
-keep public class * extends com.getcapacitor.Plugin
-keepclassmembers class * extends com.getcapacitor.Plugin {
    @com.getcapacitor.annotation.CapacitorPlugin <init>(...);
    @com.getcapacitor.PluginMethod public *;
}

# Sentry
-keep class io.sentry.** { *; }
-dontwarn io.sentry.**
