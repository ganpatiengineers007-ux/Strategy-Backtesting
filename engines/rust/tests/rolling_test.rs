use svl_engine::rolling_mean;

#[test]
fn parity_with_python_reference() {
    let r = rolling_mean(&[1.0, 2.0, 3.0, 4.0, 5.0], 3);
    assert!(r[0].is_nan() && r[1].is_nan());
    assert!((r[2] - 2.0).abs() < 1e-12 && (r[3] - 3.0).abs() < 1e-12 && (r[4] - 4.0).abs() < 1e-12);
}
