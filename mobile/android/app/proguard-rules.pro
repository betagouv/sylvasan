# Conserver les numéros de ligne et fichiers source pour les rapports Sentry
-keepattributes LineNumberTable,SourceFile
-renamesourcefileattribute SourceFile

# Capacitor : conserver le runtime interne (gestion des permissions, réflexion) et les plugins
-keep class com.getcapacitor.** { *; }
-dontwarn com.getcapacitor.**
-keep class com.capacitorjs.** { *; }
-dontwarn com.capacitorjs.**

# Sentry
-keep class io.sentry.** { *; }
-dontwarn io.sentry.**
