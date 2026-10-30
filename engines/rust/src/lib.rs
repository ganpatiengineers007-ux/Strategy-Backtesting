/// Pehle (window-1) entries NaN; baaki rolling mean (Python reference ke saath parity).
pub fn rolling_mean(values: &[f64], window: usize) -> Vec<f64> {
    let mut out = vec![f64::NAN; values.len()];
    if window == 0 {
        return out;
    }
    let mut sum = 0.0;
    for i in 0..values.len() {
        sum += values[i];
        if i >= window {
            sum -= values[i - window];
        }
        if i + 1 >= window {
            out[i] = sum / window as f64;
        }
    }
    out
}
