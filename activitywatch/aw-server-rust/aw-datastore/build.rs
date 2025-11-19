fn main() {
    // Tell Cargo to rerun this build script if migrations directory changes
    println!("cargo:rerun-if-changed=migrations");
}

