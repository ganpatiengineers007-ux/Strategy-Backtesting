use svl_engine::rolling_mean;

#[test]
fn window_zero_gives_all_nan() {
    assert!(rolling_mean(&[1.0, 2.0], 0).iter().all(|x| x.is_nan()));
}

#[test]
fn output_length_matches_input() {
    assert_eq!(rolling_mean(&[1.0, 2.0, 3.0], 2).len(), 3);
}
