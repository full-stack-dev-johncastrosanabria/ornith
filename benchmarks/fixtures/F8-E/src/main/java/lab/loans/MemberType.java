package lab.loans;

/** Borrowing limits per membership type. */
public enum MemberType {
    STANDARD(3, 14),
    STUDENT(5, 30),
    STAFF(10, 45);

    private final int maxLoans;
    private final int loanDays;

    MemberType(int maxLoans, int loanDays) {
        this.maxLoans = maxLoans;
        this.loanDays = loanDays;
    }

    public int maxLoans() {
        return maxLoans;
    }

    public int loanDays() {
        return loanDays;
    }
}
