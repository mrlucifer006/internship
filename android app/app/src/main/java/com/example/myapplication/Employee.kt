package com.example.myapplication

import kotlinx.serialization.Serializable

@Serializable
data class Employee(
    // Nullable types prevent crashes if the DB row has empty fields
    val connection_mode: String? = null,
    val public_url: String? = null
)