from utils.kpis import calculate_basic_kpis
from utils.problems import detect_problems
from utils.recommendations import generate_recommendations


def analyse_delivery_platform(dataframe):
    kpis = calculate_basic_kpis(dataframe)
    problems = detect_problems(kpis)
    recommendations = generate_recommendations(problems)

    return {
        "kpis": kpis,
        "problems": problems,
        "recommendations": recommendations,
    }