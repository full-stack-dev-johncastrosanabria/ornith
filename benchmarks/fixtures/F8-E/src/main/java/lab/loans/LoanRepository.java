package lab.loans;

import java.util.List;
import java.util.Optional;

public interface LoanRepository {
    void save(Loan loan);

    Optional<Loan> find(String loanId);

    List<Loan> openLoansOf(String memberId);

    Optional<Loan> openLoanFor(String isbn);
}
