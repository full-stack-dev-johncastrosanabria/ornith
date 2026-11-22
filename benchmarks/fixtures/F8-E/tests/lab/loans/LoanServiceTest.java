package lab.loans;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigDecimal;
import java.time.LocalDate;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class LoanServiceTest {
    private LoanService service;

    private static LocalDate d(String iso) {
        return LocalDate.parse(iso);
    }

    private static void assertMoney(String expected, BigDecimal actual) {
        assertEquals(0, new BigDecimal(expected).compareTo(actual), () -> "expected " + expected + " but was " + actual);
    }

    @BeforeEach
    void setUp() {
        service = new LoanService(new InMemoryLoanRepository(), new LoanPolicy());
        service.register(new Member("std", MemberType.STANDARD));
        service.register(new Member("stu", MemberType.STUDENT));
        service.register(new Member("staff", MemberType.STAFF));
    }

    @Test
    void weekdayDueDateIsKept() {
        assertEquals(d("2026-03-16"), service.borrow("std", "isbn-1", d("2026-03-02")).getDueOn());
    }

    @Test
    void saturdayDueDateMovesToMonday() {
        assertEquals(d("2026-03-23"), service.borrow("std", "isbn-1", d("2026-03-07")).getDueOn());
        assertEquals(d("2026-04-20"), service.borrow("staff", "isbn-2", d("2026-03-04")).getDueOn());
    }

    @Test
    void sundayDueDateMovesToMonday() {
        assertEquals(d("2026-04-06"), service.borrow("stu", "isbn-1", d("2026-03-06")).getDueOn());
    }

    @Test
    void returningOnTheDueDateIsFree() {
        Loan loan = service.borrow("std", "isbn-1", d("2026-03-02"));
        assertMoney("0.00", service.giveBack(loan.getId(), d("2026-03-16")));
    }

    @Test
    void lateFeeCountsDaysAfterTheDueDate() {
        Loan one = service.borrow("std", "isbn-1", d("2026-03-02"));
        Loan ten = service.borrow("std", "isbn-2", d("2026-03-02"));
        assertMoney("0.25", service.giveBack(one.getId(), d("2026-03-17")));
        assertMoney("2.50", service.giveBack(ten.getId(), d("2026-03-26")));
    }

    @Test
    void lateFeeIsCapped() {
        Loan loan = service.borrow("std", "isbn-1", d("2026-03-02"));
        assertMoney("10.00", service.giveBack(loan.getId(), d("2026-06-01")));
    }

    @Test
    void memberTypeLimitsOpenLoans() {
        Loan first = service.borrow("std", "isbn-1", d("2026-03-02"));
        service.borrow("std", "isbn-2", d("2026-03-02"));
        service.borrow("std", "isbn-3", d("2026-03-02"));
        assertThrows(LoanException.class, () -> service.borrow("std", "isbn-4", d("2026-03-02")));
        service.giveBack(first.getId(), d("2026-03-03"));
        service.borrow("std", "isbn-4", d("2026-03-03"));
    }

    @Test
    void bookIsLentOnceAtATime() {
        service.borrow("std", "isbn-1", d("2026-03-02"));
        assertThrows(LoanException.class, () -> service.borrow("stu", "isbn-1", d("2026-03-02")));
    }

    @Test
    void renewExtendsFromTheCurrentDueDate() {
        Loan loan = service.borrow("std", "isbn-1", d("2026-03-02"));
        Loan renewed = service.renew(loan.getId(), d("2026-03-10"));
        assertEquals(d("2026-03-30"), renewed.getDueOn());
        assertEquals(1, renewed.getRenewals());
        Loan student = service.borrow("stu", "isbn-2", d("2026-03-02"));
        assertEquals(d("2026-05-01"), service.renew(student.getId(), d("2026-03-02")).getDueOn());
    }

    @Test
    void renewalOnTheDueDateIsAllowed() {
        Loan loan = service.borrow("std", "isbn-1", d("2026-03-02"));
        assertEquals(d("2026-03-30"), service.renew(loan.getId(), d("2026-03-16")).getDueOn());
    }

    @Test
    void renewalMovesWeekendDueDateToMonday() {
        Loan loan = service.borrow("stu", "isbn-1", d("2026-03-03"));
        assertEquals(d("2026-04-02"), loan.getDueOn());
        assertEquals(d("2026-05-04"), service.renew(loan.getId(), d("2026-03-03")).getDueOn());
    }

    @Test
    void renewOnlyOnce() {
        Loan loan = service.borrow("std", "isbn-1", d("2026-03-02"));
        service.renew(loan.getId(), d("2026-03-02"));
        assertThrows(LoanException.class, () -> service.renew(loan.getId(), d("2026-03-02")));
    }

    @Test
    void overdueLoansCannotBeRenewed() {
        Loan loan = service.borrow("std", "isbn-1", d("2026-03-02"));
        assertThrows(LoanException.class, () -> service.renew(loan.getId(), d("2026-03-17")));
        assertEquals(d("2026-03-16"), loan.getDueOn());
    }

    @Test
    void returnedOrUnknownLoansCannotBeRenewed() {
        Loan loan = service.borrow("std", "isbn-1", d("2026-03-02"));
        service.giveBack(loan.getId(), d("2026-03-02"));
        assertThrows(LoanException.class, () -> service.renew(loan.getId(), d("2026-03-02")));
        assertThrows(LoanException.class, () -> service.renew("L999", d("2026-03-02")));
    }
}
