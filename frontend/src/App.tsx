import BenefitCard from "./components/BenefitCard";

function App() {
  return (
    <div>
      <h1>ShramMitra</h1>

      <BenefitCard
        category="Pension"
        schemeName="PM-SYM"
        description="Pension support for eligible unorganised workers."
        eligibilityStatus="Potentially Eligible"
      />
    </div>
  );
}

export default App;